"""
Permission system for IdeaV Local - Python version

This module implements the permission system equivalent to the PHP version's
Check_Grant(), Check_Types_Grant(), and Validate_Token() functions.

Permission Levels:
- BARRED: No access
- READ: Read-only access
- WRITE: Full read/write access

The system supports:
- Object-level access control
- Role-based permissions
- Mask-based value filtering
- Metadata editing rights
- Hierarchical permission inheritance
"""
from flask import session, request
from database import Database
from config import Config
from utils import write_log


class PermissionError(Exception):
    """Exception raised when permission is denied"""
    pass


class PermissionSystem:
    """
    Manages user permissions and access control

    This class handles:
    - Token validation
    - Role-based permission loading
    - Object-level access checking
    - Type-based access checking
    """

    def __init__(self, db_name):
        self.db_name = db_name
        self.grants = {}
        self.user = None
        self.user_id = None
        self.role = None
        self.xsrf = None

    def validate_token(self, token):
        """
        Validate authentication token and load user permissions

        Equivalent to PHP's Validate_Token() function.

        Args:
            token: Authentication token from cookie

        Returns:
            bool: True if token is valid, False otherwise

        Side effects:
            - Sets self.user, self.user_id, self.role
            - Loads permissions into self.grants
        """
        if not token:
            return False

        try:
            with Database(self.db_name) as db:
                # Find user with this token
                query = f"""
                    SELECT u.id, u.val, role_def.id r, role_def.val role,
                           xsrf.val xsrf
                    FROM `{self.db_name}` tok, `{self.db_name}` u
                    LEFT JOIN (`{self.db_name}` r CROSS JOIN `{self.db_name}` role_def)
                        ON r.up=u.id AND role_def.id=r.t AND role_def.t=%s
                    LEFT JOIN `{self.db_name}` xsrf
                        ON xsrf.up=u.id AND xsrf.t=%s
                    WHERE u.t=%s AND tok.up=u.id AND u.val=%s AND tok.t=%s
                """
                result = db.execute_one(query, (
                    Config.ROLE,
                    Config.XSRF,
                    Config.USER,
                    self.db_name,
                    Config.TOKEN
                ))

                if not result:
                    return False

                self.user = result['val'].lower()
                self.user_id = result['id']
                self.role = result['role'].lower() if result['role'] else None
                self.xsrf = result['xsrf']

                # Check if user has a role assigned
                if not result['r']:
                    raise PermissionError(
                        f"No role assigned to user {self.user}"
                    )

                # Update activity time
                db.execute(
                    f"UPDATE `{self.db_name}` SET val=%s WHERE up=%s AND t=%s",
                    (str(time.time()), self.user_id, Config.ACTIVITY),
                    commit=True
                )

                # Load grants for this role
                self._load_grants(db, result['r'])

                # Store in session
                session['user_id'] = self.user_id
                session['user_name'] = self.user
                session['role'] = self.role

                return True

        except Exception as e:
            write_log(f"Token validation error: {e}", "error", self.db_name)
            return False

    def _load_grants(self, db, role_id):
        """
        Load permissions for a role from database

        Args:
            db: Database connection
            role_id: Role ID to load grants for
        """
        # Get grants for this role
        query = f"""
            SELECT gr.val object,
                   CASE WHEN mask.t=%s THEN mask.val ELSE '' END mask,
                   CASE WHEN lev.t=%s THEN lev.val ELSE '' END level,
                   CASE WHEN lev.t!=%s THEN lev_def.val ELSE '' END mass
            FROM `{self.db_name}` gr
            JOIN `{self.db_name}` mask ON mask.up=gr.id
            LEFT JOIN (`{self.db_name}` lev CROSS JOIN `{self.db_name}` lev_def)
                ON lev.id=mask.t AND lev_def.id=lev.t AND mask.t!=%s
            WHERE gr.up=%s
        """
        grants = db.execute(query, (
            Config.MASK,
            Config.LEVEL,
            Config.LEVEL,
            Config.MASK,
            role_id
        ))

        # Process grants
        for grant in grants:
            obj = grant['object']
            mask = grant['mask']
            level = grant['level']
            mass = grant['mass']

            # Handle mask-based grants
            if mask and level:
                if 'masklevel' not in self.grants:
                    self.grants['masklevel'] = {}
                if obj not in self.grants['masklevel']:
                    self.grants['masklevel'][obj] = {}
                self.grants['masklevel'][obj][level] = mask
            elif level:
                self.grants[obj] = level
            elif mask:
                if 'mask' not in self.grants:
                    self.grants['mask'] = {}
                if obj not in self.grants['mask']:
                    self.grants['mask'][obj] = []
                self.grants['mask'][obj].append(mask)
            elif mass:
                if mass not in self.grants:
                    self.grants[mass] = {}
                self.grants[mass][obj] = ""

    def check_types_grant(self, fatal=True):
        """
        Check if user has permission to view/edit metadata types

        Equivalent to PHP's Check_Types_Grant() function.

        Args:
            fatal: If True, raise exception on denial. If False, return READ

        Returns:
            str: Permission level ("WRITE", "READ", or "BARRED")

        Raises:
            PermissionError: If user lacks permission and fatal=True
        """
        # Admin has full access
        if self.user == "admin":
            return "WRITE"

        # Check if user has explicit grant for type 0 (metadata)
        if 0 in self.grants:
            if self.grants[0] in ["READ", "WRITE"]:
                return self.grants[0]

        if fatal:
            raise PermissionError(
                f"You do not have the grant to view and edit the metadata "
                f"(current grant: {self.grants.get(0, 'NONE')})"
            )

        return "READ"

    def check_grant(self, obj_id, t=0, grant="WRITE", fatal=True):
        """
        Check if user has permission for an object

        Equivalent to PHP's Check_Grant() function.

        Args:
            obj_id: Object ID to check
            t: Type ID (0 for object itself, or specific type)
            grant: Required permission level ("READ" or "WRITE")
            fatal: If True, raise exception on denial

        Returns:
            bool: True if granted, False otherwise

        Raises:
            PermissionError: If permission denied and fatal=True
        """
        # Admin has full access
        if self.user == "admin":
            return True

        # Check explicit grant for the type
        if t != 0 and t in self.grants:
            if self.grants[t] == grant or self.grants[t] == "WRITE":
                return True
            if not fatal:
                return False
            raise PermissionError(
                f"Access denied to object {obj_id}, type {t}. "
                f"Required: {grant}, Have: {self.grants.get(t, 'NONE')}"
            )

        # Check explicit grant for the object
        if obj_id in self.grants:
            if self.grants[obj_id] == grant or self.grants[obj_id] == "WRITE":
                return True
            if not fatal:
                return False
            raise PermissionError(
                f"Access denied to object {obj_id}. "
                f"Required: {grant}, Have: {self.grants.get(obj_id, 'NONE')}"
            )

        # Query database for object hierarchy
        try:
            with Database(self.db_name) as db:
                if t == 0:
                    # Get object info
                    query = f"""
                        SELECT obj.t, COALESCE(par.t, 1) par_typ,
                               COALESCE(par.id, 1) par_id,
                               COALESCE(arr.id, -1) arr
                        FROM `{self.db_name}` obj
                        LEFT JOIN `{self.db_name}` par
                            ON obj.up>1 AND par.id=obj.up
                        LEFT JOIN `{self.db_name}` arr
                            ON arr.up=par.t AND arr.t=obj.t
                        WHERE obj.id=%s LIMIT 1
                    """
                    row = db.execute_one(query, (obj_id,))
                elif obj_id != 1:
                    # Get object info by parent and type
                    query = f"""
                        SELECT obj.t, COALESCE(par.t, 1) par_typ,
                               COALESCE(par.id, 1) par_id,
                               COALESCE(arr.id, -1) arr
                        FROM `{self.db_name}` obj
                        JOIN `{self.db_name}` par
                            ON obj.up>1 AND (par.t=obj.up OR par.id=obj.up)
                        LEFT JOIN `{self.db_name}` arr
                            ON arr.up=par.t AND arr.t=obj.t
                        WHERE par.id=%s AND (obj.t=%s OR obj.id=%s) LIMIT 1
                    """
                    row = db.execute_one(query, (obj_id, t, t))
                else:
                    # First level object
                    row = {
                        't': t,
                        'par_typ': 1,
                        'par_id': 1,
                        'arr': -1
                    }

                if row:
                    # Check type grant
                    if row['t'] in self.grants:
                        if (self.grants[row['t']] == grant or
                            self.grants[row['t']] == "WRITE"):
                            return True

                    # Check array grant
                    if row['arr'] in self.grants:
                        if (self.grants[row['arr']] == grant or
                            self.grants[row['arr']] == "WRITE"):
                            return True

                    # Check parent type grant
                    if row['par_typ'] in self.grants:
                        if (self.grants[row['par_typ']] == grant or
                            self.grants[row['par_typ']] == "WRITE"):
                            return True

                    # Check parent object grant
                    if row['par_id'] in self.grants:
                        if (self.grants[row['par_id']] == grant or
                            self.grants[row['par_id']] == "WRITE"):
                            return True

                    # Recursive check on parent
                    if row['par_id'] > 1:
                        return self.check_grant(row['par_id'], 0, grant, False)

        except Exception as e:
            write_log(f"Permission check error: {e}", "error", self.db_name)

        if fatal:
            raise PermissionError(
                f"Access denied to object {obj_id}, type {t}. "
                f"Required: {grant}, global grant: {self.grants.get(1, 'NONE')}"
            )

        return False

    def can_edit_metadata(self, obj):
        """
        Check if user can edit metadata

        Args:
            obj: Object dict with 'up' field

        Returns:
            bool: True if metadata can be edited
        """
        # Cannot edit metadata (objects with up=0)
        if obj.get('up') == 0:
            return False
        return True

    def can_delete_metadata(self, parent):
        """
        Check if user can delete metadata

        Args:
            parent: Parent object dict with 'up' field

        Returns:
            bool: True if can delete
        """
        # Cannot delete if parent is metadata (parent.up=0)
        if parent and parent.get('up') == 0:
            return False
        return True

    def has_delete_grant(self, type_id):
        """
        Check if user has DELETE permission for a specific type.

        This checks the grants['DELETE'][type_id] structure from PHP.

        Args:
            type_id: Type ID to check delete permission for

        Returns:
            bool: True if user has delete grant for this type
        """
        # Admin always has delete permission
        if self.user == "admin" or self.user == self.db_name:
            return True

        # Check if DELETE grants exist and type_id is in them
        if 'DELETE' in self.grants:
            return type_id in self.grants['DELETE']

        return False


# Global permission check functions for use in routes
def get_permission_system(db_name):
    """
    Get or create permission system for current session

    Args:
        db_name: Database name

    Returns:
        PermissionSystem: Initialized permission system
    """
    if 'permission_system' not in session or session.get('db_name') != db_name:
        perm_sys = PermissionSystem(db_name)
        token = request.cookies.get(db_name)
        if token and perm_sys.validate_token(token):
            session['permission_system'] = perm_sys
            session['db_name'] = db_name
            return perm_sys
        return None
    return session['permission_system']


def require_permission(grant="READ"):
    """
    Decorator to require permission for a route

    Usage:
        @app.route('/path')
        @require_permission("WRITE")
        def my_route():
            ...

    Args:
        grant: Required permission level ("READ" or "WRITE")
    """
    from functools import wraps

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            db_name = kwargs.get('db_name') or request.db_name
            perm_sys = get_permission_system(db_name)

            if not perm_sys:
                from flask import redirect, url_for
                return redirect(url_for('login_page', db=db_name))

            # Get object ID if present
            obj_id = kwargs.get('obj_id')
            if obj_id:
                perm_sys.check_grant(obj_id, 0, grant, fatal=True)

            return f(*args, **kwargs)

        return decorated_function
    return decorator


# Add time import
import time

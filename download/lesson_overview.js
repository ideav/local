$( '<style>.highlighted { border: 3px solid gold !important; border-radius: 15px; }'
        +'.du { border-bottom: 1px dashed; }'
    +'</style>' ).appendTo( "head" );
var lambda;
$( document ).ready(function(){
    var step=getCookie('step');
    switch(document.location.pathname.replace('/'+db+'/','')){
        case '':
        case '/'+db:
            qbHead(t9n('[RU]Быстрый обзор Интеграла[EN]Quick Ideav overview'),chm);
            qbText(t9n('[RU]<p>Это краткая экскурсия по системе. Я покажу, где тут что находится. Следуйте подсказкам, а я буду подсвечивать <span class="highlighted">&nbsp;золотом&nbsp;</span> то, на что нужно обратить внимание.</p>'
                        +'<p>Вы можете перетаскивать это окно мышью или двигать стрелками на вашем мобильном устройстве и изменять размер шрифта кнопкой Т справа вверх уэтого окна.</p>'
                        +'[EN]<p>This is a quick tour through Ideav. Follow my tips, while I would put a <span class="highlighted">&nbsp;golden&nbsp;</span> mark on the elements you need to process.</p>'
                        +'<p>You may drag&drop this window using mouse or move it with arrows on your mobile. You may shrink the font size with the T button in the upper right corner of this window.</p>')
                +'<p>'+t9n('[RU]Нажмите[EN]Press')+'&nbsp; <a class="btn btn-sm btn-outline-secondary mb-2" href="/'+db+'/info">'+t9n('[RU]Продолжить[EN]Continue')+'</a></p>'
                );
            break;
        case 'info':
            qbHead(t9n('[RU]Быстрый обзор Интеграла[EN]Quick Ideav overview'),chm);
            qbText(t9n('[RU]Вы видите меню со ссылками на часто используемые рабочие места. Давайте рассмотрим их одно за другим.'
                +'[EN]You may see the upper menu with links to the most useful workplaces of Ideav. Let\'s inspect these one by one.'));
            goMenu('object/18');
            break;
        case 'edit_types':
            qbHead(t9n('[RU]Редактор структуры таблиц[EN]Tables structure editor'),chm,'0');
            qbText(t9n('[RU]<p>В этом рабочем месте мы редактируем структуру наших таблиц: состав колонок, связи с другими таблицами, обязательные и вычисляемые поля, кнопки контекстных действий и прочее.</p>'
                    +'<p>Здесь можно создать сколько угодно большую структуру взяимосвязанных данных, и мы сделаем это в следующих уроках.</p>'
                +'[EN]<p>Here we edit the structure of our tables: the set of columns, links to other tables, mandatory and calculated fields, context action buttons, etc.</p>'
                    +'<p>You can create a structure of interconnected data of any complexity, and we will do this in our lessons.</p>'
                )
                +'<a class="btn btn-sm btn-outline-secondary mb-2" onclick="lambda()">'+t9n('[RU]Продолжить[EN]Continue')+'</a>'
            );
            lambda=function(){
                    qbHead(t9n('[RU]Меню Файлы[EN]Directory manager'),chm,'0');
                    qbText(t9n('[RU]<p>Мы не рассмотрели меню '+menu[getMenuName('dir_admin')].name+'.</p>'
                            +'<p>Кликните его, чтобы попасть в это специализированное рабочее место&nbsp;&mdash; оно откроется в отдельной закладке, где вы сможете почитать его описание, а потом возвращайтесь сюда, закрыв ту закладку!</p>'
                        +'[EN]<p>We have just one menu item left: '+menu[getMenuName('dir_admin')].name+'.</p>'
                            +'<p>Click it to get to this specialized workspace&nbsp;&mdash; it will open in a separate tab where you can read its description, and then come back here after closing that tab!</p>'
                        )
                    );
                    highlightMenu('dir_admin');
                    $('a[href="/'+db+'/dir_admin"]').attr('target','_blank').click(function(){lambda()});
                    lambda=function(){
                        $('.highlighted').removeClass('highlighted');
                        qbHead(t9n('[RU]Личный кабинет[EN]Private space'),chm,'0');
                        $('#navbarDropdown,#brand,a[href="/my?u='+db+'"]').addClass('highlighted');
                        qbText(t9n('[RU]<p>На этом обзор системы закончен, и вы можете перейти к следующему уроку на домашней странице вашего Интеграла (ссылка слева вверху) или изучить свой личный кабинет.</p>'
                                +'<p>В правом верхнем меню вы увидите ссылки на сайт руководства Интеграла, личный кабинет, переключение языка и смену пароля.</p>'
                                +'<p>Спасибо!</p>'
                            +'[EN]<p>This completes the review of the system, and you may start the next lesson on the home page or explore your personal account.</p>'
                                +'<p>In the upper right menu you will see links to the Integral management website, personal account, language switching and password change.</p>'
                                +'<p>Thank you!</p>')
                        );
                        $('.stop-confirm').remove();
                        document.cookie='_qip=;max-age=0;Path=/'+db;
                    };
                };
            break;
        case 'form':
            qbHead(t9n('[RU]Простой конструктор форм[EN]Quick form builder'),chm,'0');
            qbText(t9n('[RU]<p>Здесь вы можете быстро создать форму для добавления объектов, отображения отчетов, графиков и сводных таблиц.</p>'
                    +'<p>Изначально список форм пуст, но в следующих уроках мы создадим здесь форму со всеми этими популярными элементами.</p>'
                +'[EN]<p>Here you can quickly create a form to add objects, display reports, graphs and pivot tables.</p>'
                    +'<p>Initially, the list of forms is empty, and in our tutorials we will create a form with all these popular elements.</p>'
                ));
            goMenu('sql');
            break;
        case 'sql':
            qbHead(t9n('[RU]Конструктор запросов[EN]Query builder'),chm,'0');
            qbText(t9n('[RU]<p>Это самое мощное средство работы с данными, какое вы можете найти в конструкторах без кода.</p>'
                    +'<p>Вы видите здесь несколько служебных запросов, которые используются для отображения страниц Интеграла, включая эту&nbsp;&mdash; главное меню и список запросов построены на основе этих запросов.</p>'
                    +'<p>В наших уроках мы будем делать здесь выборки данных из любого количества связанных таблиц, будем применять вычисления, использовать вложенные запросы и вызовы к внешним системам (email-, sms-шлюзы и подобные вызовы).</p>'
                +'[EN]I bet, this is the most powerful data manipulation tool you can find in no-code constructors.'
                    +'<p>You see several service queries here that are used to display Ideav pages, including this one&nbsp;&mdash; the main menu and list of reports are built based on these reports.</p>'
                    +'<p>In our lessons, we will make data selections here from any number of related tables, we will apply calculations, use nested queries and calls to external systems (email, sms gateways, etc.).</p>'
                ));
            goMenu('upload');
            break;
        case 'dict':
            qbHead(t9n('[RU]Таблицы данных Интеграла[EN]Ideav data tables set'),chm,'0');
            qbText(t9n('[RU]<p>Это список таблиц, которые хранятся в вашей базе данных.</p>'
                    +'<p>Вы видите таблицы пользователей, ролей, запросов&nbsp;&mdash; это всё независимые таблицы. А вот таблицы Меню и Объектов, которые входят в Роль, здесь не видны. Они не независимые, а подчинены роли.</p>'
                    +'<p>Кликните таблицу <i>Запрос</i>, чтобы посмотреть её содержимое.</p>'
                +'[EN]This is a list of tables that are stored in your database.'
                    +'<p>You see tables of users, roles, requests&nbsp;&mdash; these are all independent tables. The Menu and Objects tables that are included in the Role, are not visible here. They are not independent, but subordinate to the role.</p>'
                    +'<p>Click the table named <i>Query</i>, to see its content.</p>'
                ));
            $('div[onclick*="object/22\'"]').addClass('highlighted');
            break;
        case 'upload':
            qbHead(t9n('[RU]Экспресс-загрузка таблиц[EN]Instant import of data'),chm,'0');
            qbText(t9n('[RU]<p>Здесь вы можете загрузить вашие данные в Интеграл, просто скопировав таблицу из экселя или текстового файла. Система распознает тип данных и имена полей.</p>'
                    +'<p>Вы сможете настроить импорт: поменять колонки таблицы местами, вычислить значения, подсчитать статистику для предварительной проверки корректности распознавания. Все настройки будут сохранены, и вы можете использовать их при последующем импорте данных.</p>'
                +'[EN]<p>Here you can upload your data to Ideav simply by copying the table from an excel file or a text file. The system recognizes the data types and field names.</p>'
                    +'<p>You can set up the import: swap table columns, calculate values, watch statistics to verify the recognition correctness. All settings will be saved and you can use them when importing data later.</p>'
                ));
            goMenu('dict');
            break;
        case 'object/22/':
        case 'object/22':
            qbHead(t9n('[RU]Таблица запросов[EN]The queries table'),chm,'0');
            qbText(t9n('[RU]<p>Это список запросов, которые существуют в системе. Запрос&nbsp;&mdash; это набор полей произвольных таблиц с применением фильтрации, сортировки, группировки и вычислений.</p>'
                    +'<p>В поле <i>Колонки запроса</i> видно, сколько полей данных выбрано из базы данных для этого запроса.'
                    +' <b>Кликните <span class="highlighted">ссылку на колонки запроса</span></b> <i>MyRoleMenu</i>, чтобы посмотреть содержимое этой подчиненной таблицы.</p>'
                +'[EN]<p>This is a list of queries that exist in the system. A query is a set of fields of arbitrary tables with filtering, sorting, grouping and calculations applied.</p>'
                    +'<p>The <i>Query fields</i> column shows how many data fields have been selected from the database for this query.'
                    +' <b>Click the <span class="highlighted">link to query fields</span></b> of <i>MyRoleMenu</i> to view the contents of this subtable.</p>'
                ));
            $('a[href$="28/?F_U=169"]').addClass('highlighted');
            break;
        case 'object/28/':
            qbHead(t9n('[RU]Таблица Колонок запроса[EN]The Query fields table'),chm,'0');
            qbText(t9n('[RU]<p>Это подчиненная таблица запроса <i>MyRoleMenu</i>, здесь перечислены поля данных этого запроса, выбранные из разных таблиц: Пользователь, Роль, Меню.</p>'
                    +'<p>К данным применен фильтр [USER_ID]&nbsp;&mdash; текущий пользователь&nbsp;&mdash; это вы, применены функции, назначены имена Name и HREF, часть полей скрыта в отчете.</p>'
                    +'<p>Кликните <span class="highlighted">ссылку на запрос</span></b> <i>MyRoleMenu</i>, чтобы открыть форму его редактирования.</p>'
                +'[EN]<p>This is a sub table of the <i>MyRoleMenu</i> query, here are the query data fields selected from different tables: User, Role, Menu.</p>'
                    +'<p>The [USER_ID] filter has been applied to the data&nbsp;&mdash; the current user&nbsp;&mdash; it is you, functions have been applied, the Name and HREF names have been assigned, some of the fields are hidden in the report.</p>'
                    +'<p>Click the <span class="highlighted">reference</span></b> to <i>MyRoleMenu</i> to open the edit form.</p>'
                ));
            $('a[href$="edit_obj/169"]').addClass('highlighted');
            break;
        case 'edit_obj/'+uid:
        case 'edit_obj/'+uid+'/':
            qbHead(t9n('[RU]Форма редактирования записи[EN]The record edit form'),chm,'0');
            $('.stop-confirm').remove();
            qbText('<div class="qip1" this-s="qip1">'
                +t9n('[RU]<p>Это форма редактирования записи, в данном случае - это запись о вас как пользователе.</p>'
                    +'<p>У вас есть роль Admin - администратор, с полным доступом к системе. Также здесь хранятся ваши email (для сброса пароля) и телефон, дата вашей регистрации, имя, зашифрованный пароль и токены.</p>'
                +'[EN]<p>This is the editing form, in this case you may edit the record about yourself as a user.</p>'
                    +'<p>You have the Admin role - the administrator with full access to the system. It also stores your email (for password reset) and phone number, your registration date, name, encrypted password and tokens.</p>')
                +'<a class="btn btn-sm btn-outline-secondary mb-2" onclick="nextTab(this);goMenu(\'sql\')">'+t9n('[RU]Продолжить[EN]Continue')+'</a>'
                +'</div>'
                );
            qbText('<div class="qip2 qip1" this-s="qip2" style="display:none">'
                +t9n('[RU]<p>Это стандартная форма редактирования объектов в Интеграле - любая таблица представлена в виде набора колонок разных типов, и поля их ввода выглядят по-разному.</p>'
                    +'<p><b>Вы заходите в систему как <i>'+$('#t18').val()+'</i> - не меняйте здесь это имя или Роль <i>admin</i>, иначе не сможете войти!</b></p>'
                +'[EN]<p>This is a standard form for editing objects in Integral - any table is presented as a set of columns of different types, and their input fields look different.</p>'
                    +'<p><b>You are logged in as <i>'+$('#t18').val()+'</i> - don\'t change this name here or Role <i>admin</i > otherwise you won\'t be able to log in!</b></p>')
                +'</div>');
            break;
        case 'edit_obj/169':
            qbHead(t9n('[RU]Форма редактирования запроса[EN]The Query edit form'),chm,'0');
            qbText(t9n('[RU]Это форма редактирования запроса, здесь мы видим и можем редактировать все его свойства.'
                    +'<p>Мы также можем добавить любое количество свойств любому объекту в Интеграле. Это делается в меню Структура&nbsp;&mdash; там мы будем редактировать состав полей наших таблиц.</p>'
                +'[EN]This is the edit form, here we see and can edit all the query properties.'
                    +'<p>We can also add any properties to any object in Ideav. We will do it in the Structure menu&nbsp;&mdash; there we edit the set of the fields of our tables.</p>'
                ));
            goMenu('edit_types');
            break;
        case 'object/18/':
        case 'object/18':
            qbHead(t9n('[RU]Таблица и элементы управления[EN]Table of items and its controls'),chm,'0');
            qbText('<div class="qip1" this-s="qip1"'+(document.location.search==''?'':' style="display:none"')+'>'
                +t9n('[RU]<p>Это список пользователей, зарегистрированных в этой базе Интеграла. Изначально в списке только один пользователь&nbsp;&mdash; администратор.</p>'
                    +'<p>Администратор может добавлять сюда других пользователей, назначая им <i>Роль</i>, а для <i>Роли</i> можно задавать доступы к таблицам и рабочим местам системы.</p>'
                +'[EN]<p>This is the list of registered users: you may see the admin. Initially, there is only one user&nbsp;&mdash; the administrator named the same as your database.</p>'
                    +'<p>The administrator can add other users here and assign a <i>Role</i> to them. <i>Roles</i> define the access to tables and system workplaces.</p>')
                +'<a class="btn btn-sm btn-outline-secondary mb-2" onclick="nextTab(this);highlightBtn(\'plus.png\');">'+t9n('[RU]Продолжить[EN]Continue')+'</a>'
                +'</div>'
                );
            qbText('<div class="qip2 qip1" this-s="qip2" style="display:none">'
                +t9n('[RU]<p>Над таблицей есть меню для управления ей.</p>'
                    +'<p> Кнопкой (+) вы сможете добавить объект в эту таблицу&nbsp;&mdash; кнопка выделена золотым, найдите её. Мы будем добавлять объекты в следующих уроках.</p>'
                +'[EN]<p>Above the table there is a menu to manage it. With the (+) button you can add an object to this table&nbsp;&mdash; we will do this in the next lessons.</p>')
                +'<a class="btn btn-sm btn-outline-secondary mb-2" onclick="nextTab(this);highlightBtn(\'refresh.png\');">'+t9n('[RU]Продолжить[EN]Continue')+'</a>'
                +'</div>'
                );
            qbText('<div class="qip2 qip3" this-s="qip3" style="display:none">'
                +t9n('[RU]<p>Эта кнопка&nbsp;&mdash; обновление содержимого таблицы. Кто-то мог внести изменения, и мы увидим их, обновляя таблицу.</p>'
                    +'[EN]<p>The next button is to update the contents of the table. Someone may have made changes and we will see them by updating the table.</p>')
                    +'<a class="btn btn-sm btn-outline-secondary mb-2" onclick="nextTab(this);highlightBtn(\'resize.png\');highlightBtn(\'collapse.png\',true);">'+t9n('[RU]Продолжить[EN]Continue')+'</a>'
                    +'</div>'
                );
            if(step==='refresh.png'){
                $('div[this-s="qip3"]').show();
                qbText('<div class="qip3">'
                    +t9n('[RU]<b>Вы только что обновили таблицу.</b>'
                        +'[EN]<b>You have just refreshed the table.</b>')
                    +'</div>');
                highlightBtn(step);
            }
            qbText('<div class="qip4 qip3" this-s="qip4" style="display:none">'
                +t9n('[RU]<p>Эта кнопка&nbsp;&mdash; управление компактностью таблицы.</p><p><b>Нажмите эту кнопку несколько раз, чтобы посмотреть как она работает.</b></p>'
                         +'<p>Система запомнит выбранную компактность в этом браузере.</p>'
                   +'[EN]<p>This button is to control the compactness of the table.</p><p><b>Click it several times to see how it works.</b></p>'
                         +'<p>The system will remember the selected compactness in this browser.</p>')
                    +'<a class="btn btn-sm btn-outline-secondary mb-2" onclick="nextTab(this);highlightBtn(\'filter.png\');highlightBtn(\'clear-filters.png\',true);">'+t9n('[RU]Продолжить[EN]Continue')+'</a>'
                    +'</div>'
                );
            qbText('<div class="qip4 qip5" this-s="qip5" style="display:none">'
                +t9n('[RU]<p>Следующие две кнопки служат для управления фильтром на таблице. <b>Нажмите <img class="icon8" src="https://img.icons8.com/ios/25/333333/filter.png"> один раз, чтобы отобразить поля фильтров.</b></p>'
                        +'<p>Вы можете задать условия отбора по любому полю таблицы, чтобы выбрать нужные вам данные.</p>'
                        +'<p>Кнопка <img class="icon8" src="https://img.icons8.com/ios/25/333333/clear-filters.png"> очищает фильтры и сортировку таблицы.</p>'
                    +'[EN]<p>The next two buttons are used to control the filter on the table. <b>Press <img class="icon8" src="https://img.icons8.com/ios/25/333333/filter.png"> once.</b></p>'
                        +'<p>You can set selection conditions for any field of the table to select the data you need.</p>'
                        +'<p>This button: <img class="icon8" src="https://img.icons8.com/ios/25/333333/clear-filters.png"> clears the filters and order of the table.</p>'
                    )
                    +'<a class="btn btn-sm btn-outline-secondary mb-2" onclick="nextTab(this);highlightBtn(\'flow-chart.png\');">'+t9n('[RU]Продолжить[EN]Continue')+'</a>'
                +'</div>'
                );
            if(step==='clear-filters.png'){
                $('div[this-s="qip5"]').show();
                qbText('<div class="qip5">'
                    +t9n('[RU]<b>Вы только что очистили фильтр и сортировку в таблице этой кнопкой.</b>'
                        +'[EN]<b>You have just cleared the filter and sorting in the table with this button.</b>')
                    +'</div>');
                highlightBtn(step);
            }
            if(step==='filter.png'){
                $('div[this-s="qip5"]').show();
                if($('input[name=F_18]').is(':visible'))
                    qbText('<div class="qip5">'
                        +t9n('[RU]<b>Вы применили фильтр к таблице.</b>'
                            +'[EN]<b>You have just applied a filter to the table.</b>')
                        +'</div>');
                else
                    qbText('<div class="qip5">'
                        +t9n('[RU]<b>Вы применили пустой фильтр к таблице этой кнопкой.</b>'
                            +'[EN]<b>You have just applied an empty filter to the table with this button.</b>')
                        +'</div>');
                highlightBtn(step);
            }
            qbText('<div class="qip6 qip5" this-s="qip6" style="display:none">'
                +t9n('[RU]<p>Эта кнопка покажет связи записей в этой таблицы&nbsp;&mdash; те объекты, которые ссылаются на эту запись. Это бывает удобно для поиска записей, которые ссылаются на это значение, например, выбрать всех клиентов нужной вам категории, не заходя в справочник клиентов.</p>'
                    +'[EN]<p>This button will show links to external objects that refer this table&nbsp;&mdash; those objects that refer to this record. This can be useful for finding records that refer to this value, for example, to select all customers of the category you need without visiting the customer directory.</p>'
                )
                +'<a class="btn btn-sm btn-outline-secondary mb-2" onclick="nextTab(this);highlightBtn(\'grid.png\');">'+t9n('[RU]Продолжить[EN]Continue')+'</a>'
                +'</div>'
                );
            if(step==='flow-chart.png'){
                $('div[this-s="qip6"]').show();
                qbText('<div class="qip6">'
                    +t9n('[RU]<b>Вы переключили режим отображения связей&nbsp;&mdash; ссылка на связанные справочники будет отображаться в последней колонке таблицы&nbsp;&mdash; <i>Связи</i>.</b>'
                        +'[EN]<b>You have switched the references display mode. References to linked directories, if any, will be displayed in the last column of the table&nbsp;&mdash; <i>References</i>.</b>')
                    +'</div>');
                highlightBtn(step);
            }
            qbText('<div class="qip6 qip7" this-s="qip7" style="display:none">'
                +t9n('[RU]<p>Ещё одна кнопка для управления компактностью, включающая многорядный режим для больших таблиц. Это редко используемый режим.</p>'
                    +'[EN]<p>Another button to control compactness, using multi-row mode for vast tables. It is rarely used.</p>'
                )
                +'<a class="btn btn-sm btn-outline-secondary mb-2" onclick="nextTab(this);highlightBtn(\'view-details.png\');">'+t9n('[RU]Продолжить[EN]Continue')+'</a>'
                +'</div>'
                );
            qbText('<div class="qip8 qip7" this-s="qip8" style="display:none">'
                +t9n('[RU]<p>Эта кнопка отображает содержимое ячеек таблицы полностью, в то время как в обычном режиме оно сокращено до 127 символов.</p>'
                    +'[EN]<p>This button displays the full contents of cells of the table, while in normal mode it is reduced to 127 characters.</p>'
                )
                +'<a class="btn btn-sm btn-outline-secondary mb-2" onclick="nextTab(this);highlightBtn(\'database-export.png\');highlightBtn(\'database-restore.png\',true);highlightBtn(\'export-csv.png\',true);">'+t9n('[RU]Продолжить[EN]Continue')+'</a>'
                +'</div>'
                );
            if(step==='view-details.png'){
                $('div[this-s="qip8"]').show();
                if($('#fullbtn').hasClass('icon8-1'))
                    qbText('<div class="qip8">'
                        +t9n('[RU]<b>Вы ВКЛЮЧИЛИ режим полного отображения полей.</b>'
                            +'[EN]<b>You have switched ON the full cell display mode.</b>')
                        +'</div>');
                else
                    qbText('<div class="qip8">'
                        +t9n('[RU]<b>Вы ВЫКЛЮЧИЛИ режим полного отображения полей.</b>'
                            +'[EN]<b>You have switched OFF the full cell display mode.</b>')
                        +'</div>');
                highlightBtn(step);
            }
            qbText('<div class="qip8 qip9" this-s="qip9" style="display:none">'
                +t9n('[RU]<p>Эти три кнопки служат для импорта и экспорта данных в эту таблицу.</p>'
//                        +'<p><b>Нажмите <img class="icon8" src="https://img.icons8.com/ios/25/333333/export-csv.png">, чтобы выгрузить таблицу пользователей в файл CSV.</b>.</p>'
                    +'[EN]<p>These three buttons are used to import and export data to this table..</p>'
//                        +'<p><b>Click <img class="icon8" src="https://img.icons8.com/ios/25/333333/export-csv.png"> to export the users table to a CSV file.</b>.</p>'
                )
                +'<a class="btn btn-sm btn-outline-secondary mb-2" onclick="nextTab(this);highlightBtn(\'delete.png\');">'+t9n('[RU]Продолжить[EN]Continue')+'</a>'
                +'</div>'
                );
            qbText('<div class="qip10 qip9" this-s="qip10" style="display:none">'
                +t9n('[RU]<p>Этой кнопкой можно удалить записи в таблице, которые удовлетворяют заданным в ней фильтрам.</p>'
                        +'<p>Вы не можете удалить себя как пользователя из таблицы пользователей&nbsp;&mdash; система осуществляет такую проверку.</p>'
                    +'[EN]<p>With this button, you can delete records in the table that match the filters specified in it.</p>'
                        +'<p>You cannot remove yourself as a user from the user table&nbsp;&mdash; the system performs such a check.</p>'
                )
                +'<a class="btn btn-sm btn-outline-secondary mb-2" onclick="nextTab(this);highlightBtn(\'settings.png\');">'+t9n('[RU]Продолжить[EN]Continue')+'</a>'
                +'</div>'
                );
            qbText('<div class="qip10 qip11" this-s="qip11" style="display:none">'
                +t9n('[RU]<p>Эта кнопка служит для настройки вида меню. Настройка запоминается в этом браузере и применяется для всех таблиц.</p>'
                        +'<p><b>Нажмите кнопку настройки и выберите подходящий вам внешний вид меню.</b></p>'
                    +'[EN]<p>This button is used to customize the appearance of the menu. The setting is remembered in this browser and applied to all tables.</p>'
                        +'<p><b>Click the settings button and choose the menu appearance that suits you.</b></p>'
                )
                +'<a class="btn btn-sm btn-outline-secondary mb-2" onclick="nextTab(this);$(\'a[href$='+uid+']\').addClass(\'highlighted\')">'+t9n('[RU]Продолжить[EN]Continue')+'</a>'
                +'</div>'
                );
            qbText('<div class="qip12 qip11" this-s="qip12" style="display:none">'
                    +'<p>'+t9n('[RU]Теперь вы знаете назначение кнопок управления таблицей&nbsp;&mdash; понажимайте их, чтобы исследовать их поведение'
                        +'[EN]Now you know the purpose of the table control buttons&nbsp;&mdash; click them to explore their behavior')+'.</p>'
                    +'<p>'+t9n('[RU]Затем кликните имя пользователя <i>'+$('a[href$='+uid+']').html()+'</i> в левой колонке таблицы, чтобы открыть форму его редактирования'
                        +'[EN]<p>Then click <i>'+$('a[href$='+uid+']').html()+'</i> in the leftmost column to open it for editing')+'.</p>'
                +'</div>');
            if($('div[this-s]').is(':visible')===false)
                qbText('<div>'+t9n('[RU]Нажимайте кнопки управления таблицей, чтобы исследовать их поведение, или начните обзор этой страницы <a href="/'+db+'/object/18">с начала</a>.'
                            +'[EN]Press the table control buttons to explore their behavior, or start their overview from the <a href="/'+db+'/object/18">beginning</a>.')
                    +'</div>');
            break;
    }
    $('#controls').find('a[title]').click(function(){
        document.cookie='step='+$(this).find('img').attr('src').split('/').pop()+';max-age=30;Path=/'+db;
    });
});
function nextTab(el){
    $('.'+$(el).parent().attr('this-s')).toggle(300);
}
function highlightBtn(s,add){
    if(!add)
        $('.highlighted').removeClass('highlighted');
    $('img[src$="'+s+'"]').addClass('highlighted');
}
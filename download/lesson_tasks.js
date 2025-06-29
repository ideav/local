function intApi(m,u,b,vars,index){ // Параметры: метод, адрес, действие - ветка switch, параметры, ID целевого элемента
    vars=vars||''; // По умолчанию список параметров пуст
    var h='',i,j,json,obj=new XMLHttpRequest(); // Объявляем переменную под JSON и API по HTTPS
    obj.open(m,'/'+db+'/'+u,true); // Открываем асинхронное соединение заданным методом по нужному адресу
    if(m=='POST'){ // Если это POST запрос, то передаем заданные параметры
        if(typeof vars=='object')
            vars.append('_xsrf',xsrf);
        else{
            obj.setRequestHeader('Content-Type','application/x-www-form-urlencoded');
            vars='_xsrf='+xsrf+'&'+vars; // добавляем токен xsrf, необходимый для POST-запроса
        }
    }
    obj.onload=function(e){ // Когда запрос вернет результат - сработает эта функция
        try{ // в this.responseText лежит ответ от сервера
            json=JSON.parse(this.responseText); // Пытаемся разобрать ответ как JSON
        }
        catch(e){ // Если произошла ошибка при разборе JSON
            console.log(e); // то выводим детали этой ошибки в консоль браузера
            console.log(this.responseText);
        }
        obj.abort(); // Закрываем соединение
        switch(b){ // Отрабатываем заданную команду - переходим в соответствующую ветку case
            case 'Create Task':
                for(i in json.edit_types[0]){
                    j=json.edit_types[0][i];
                    if(types[j]===undefined)
                        types[j]={ t:json.edit_types[1][i],r:json.edit_types[1][i],u:json.edit_types[1][i],v:json.edit_types[4][i] };
                    if(json.edit_types[1][i]!==''){
                        if(reqs[j]===undefined)
                            reqs[j]={};
                        reqs[j][json.edit_types[7][i]]={ i:json.edit_types[5][i],t:json.edit_types[6][i],a:json.edit_types[8][i],r:json.edit_types[9][i] };
                    }
                }
                for(i in preDef)
                    if(!typeExists(preDef[i].v))
                        intApi('POST','_d_new?next_act=nul','','val='+preDef[i].v+'&t='+preDef[i].t);
                idObj=idTask=typeExists(t9n('[RU]Задача[EN]Task'));
                if(!idTask){
                    qbHead(t9n('[RU]Создание таблицы Задач[EN]Setting up the Tasks table'),chm);
                    if(!curMenu('edit_types')){
                        qbText('<div class="two-step">'
                                +t9n('[RU]<p>Мы создадим простое приложение для хранения задач, и по аналогии вы сможете создавать подобные приложения под ваши требования. Следуйте подсказкам, а я буду подсвечивать <span class="highlighted">&nbsp;золотом&nbsp;</span> нужные вам элементы управления.</p>'
                                    +'<p>Вы можете перетаскивать это окно мышью или двигать стрелками на вашем мобильном устройстве.</p>'
                                    +'[EN]<p>We will create a simple app to store your tasks, so that you could easily create similar apps for your needs. Follow my tips, while I would put a <span class="highlighted">&nbsp;golden&nbsp;</span> mark on the elements you need to process.</p>'
                                    +'<p>You may drag&drop this window using mouse or move it with arrows on your mobile.</p>')
                            +'</div>');
                        goMenu('edit_types',t9n('[RU]Структура[EN]Structure'));
                    }
                    else
                        qbText('<div class="two-step">'
                                +t9n('[RU]<p>Это список объектов, которым уже обучена система. Здесь есть то, что нужно любому проекту: Пользователь, Роль, Запрос и некоторые другие.</p><p>Объект&nbsp;&mdash; это предмет (или термин) из вашей задачи автоматизации. Вы можете описывать здесь любые термины из вашей жизни, складывая из них сколько угодно сложные структуры данных.</p>'
                                    +'[EN]<p>This is the list of those objects Ideav already knows. These are essential for every project: a user, role, query and some others.</p><p>An object is a term you use in your business. Here you may define any term you need, and compose data structures of any complexity.</p>')
                            +'</div>'
                            +'<a class="btn btn-sm btn-outline-secondary two-step" onclick="$(\'.two-step\').toggle(300)">'+t9n('[RU]Продолжить[EN]Continue')
                            +'</a><div class="two-step" style="display:none">'
                            +t9n('[RU]<p>Чтобы вам не трудитьcя вводить значения, вы можете кликать синие ссылки в этом сообщении&nbsp;&mdash; я введу текст за вас.</p>'
                            +'<p>Результат будет выглядеть <a target="_blank" href="/i/ziel.png">примерно так</a>.</p>'
                            +'<p>Введите в желтом поле название вашего объекта: <a class="du" onclick="$(\'#val\').val(this.innerHTML)">Задача</a>, выберите базовый тип <a class="du" onclick="$(\'select[name=t] option[value=3]\').prop(\'selected\',true)">SHORT</a> (он стоит по умолчанию) и нажмите <i>Создать</i>.</p>'
                            +'[EN]To make it easier, I would type in the values for you when you click the blue links in this window.</p>'
                            +'<p>The result would be something <a target="_blank" href="/i/ziel_en.png">like this</a>.</p>'
                            +'<p>Fill in the yellow field with the name of your term: <a class="du" onclick="$(\'#val\').val(this.innerHTML)">Task</a>, select its type: <a class="du" onclick="$(\'select[name=t] option[value=3]\').prop(\'selected\',true)">SHORT</a> (it is set by default), and press <i>Create</i>.')
                            +'</div>');
                    $('#val,#baseTypes').addClass('highlighted');
                    return;
                }
                var step;
                if(!reqExists(idTask,t9n('[RU]Дата[EN]Date'))){
                    h='<div class="qip1" id="qip1" next-step="qip2"><p>'
                        +t9n('[RU]Добавьте Задаче свойство Дата, чтобы получить напоминание в этот день. Для этого найдите термин <a class="du" onclick="$(\'#val\').val(\'Задач\').keyup()">Задача</a> и кликните её.'
                        +'<p>Вы увидите кнопку <i>Добавить свойство</i>, перед которой в выпадающем списке вам нужно выбрать <i>Дата</i>&nbsp;&mdash; система уже знает такой термин. Нажмите <i>Добавить свойство</i>, чтобы добавить его к вашему термину <i>Задача</i>.</p>'
                        +'[EN]Add the Date property to the Task to be reminded on that day. To do so, find the term named <a class="du" onclick="$(\'#val\').val(\'Задач\').keyup()">Task</a> and click it.</p>'
                        +'<p>You will see the <i>Add attribute</i> button, and near that there is a dropdown list where you can find <i>Date</i>&nbsp;&mdash; the system already knows that term. Press <i>Add attribute</i> to make Date an attribute of the Task.')
                        +'</div>';
                    $('#val').addClass('highlighted');
                    $('#val,#id'+idTask).closest('.card-header').addClass('highlighted');
                    step='qip1';
                    checkActionqip1=function(i){
                        return byId('req'+i).innerHTML.indexOf('title="date">'+t9n('[RU]Дата[EN]Date')+'<')>0;
                    };
                }
                if(!reqExists(idTask,t9n('[RU]Срок[EN]Deadline'))){
                    h+='<div class="qip1 qip2" id="qip2" next-step="qip3"'+isFirst(step)+'><p>'
                        +t9n('[RU]Теперь добавим ещё одно понятие, которое пока неизвестно системе&nbsp;&mdash; срок выполнения задачи. Выберите в выпадающем списке <i>добавить новое</i> и добавьте свойство <a class="du" onclick="if($(\'#input'+idTask+'\').is(\':visible\'))$(\'#input'+idTask+'\').val(this.innerHTML).keyup()">Срок</a> с базовым типом <i>DATE</i>.</p><p>Кнопка <i>Создать</i> будет активна когда вы заполните эти поля верно.'
                            +'[EN]Now could you please add another attribute&nbsp;&mdash; Deadline. The system does not know it yet. Choose <i>add new</i> in the dropdown list and add <a class="du" onclick="if($(\'#input'+idTask+'\').is(\':visible\'))$(\'#input'+idTask+'\').val(this.innerHTML).keyup()">Deadline</a> with the base type name <i>DATE</i>.</p><p>The <i>Add</i> button will become active when you fill these fields in correctly.')
                            +'</p></div>';
                    step=step||'qip2';
                    checkActionqip2=function(i){
                        $('.highlighted').removeClass('highlighted');
                        $('#sel'+i).addClass('highlighted');
                        $('#newtypbtn'+i).prop('disabled',!($('#input'+i).val()===t9n('[RU]Срок[EN]Deadline')&&$('#t'+i).val()==='9'));
                        return byId('req'+i).innerHTML.indexOf('title="date">'+t9n('[RU]Срок[EN]Deadline')+'<')>0;
                    };
                }
                if(!reqExists(idTask,t9n('[RU]Описание[EN]Description'))){
                    h+='<div class="qip2 qip3" id="qip3" next-step="qip4"'+isFirst(step)+'><p>'
                        +t9n('[RU]Теперь добавьте <i>Описание</i> задачи, оно есть в списке свойств с базовым типом <i>MEMO</i>&nbsp;&mdash; оно будет выводиться на форме как многострочное поле ввода.'
                            +'[EN]Now add the <i>Description</i> of the task, it already exists in the dropdown list of registered attributes. Please note, it has the MEMO base type, and it would appear as a multi-line input field in your forms.')+'</p></div>';
                    step=step||'qip3';
                    checkActionqip3=function(i){
                        $('#sel'+i).addClass('highlighted');
                        return byId('req'+i).innerHTML.indexOf('title="memo">'+t9n('[RU]Описание[EN]Description')+'<')>0;
                    };
                }
                //' Их можно удалять или перемещать. Вы можете добавить другие нужные вам свойства, например, фото или примечание.'
                if(!reqExists(idTask,t9n('[RU]Фото[EN]Photo'))){
                    h+='<div class="qip4 qip3" id="qip4" next-step="qip5"'+isFirst(step)+'><p>'
                        +t9n('[RU]Мы захотим прикладывать к задачам фото&nbsp;&mdash; добавьте свойство <i>Фото</i> к задаче, оно также уже есть в списке свойств, его тип&nbsp;&mdash; <i>FILE</i>.'
                            +'[EN]We would like to attach photos to our tasks&nbsp;&mdash; add the <i>Photo</i> attribute to your task. It is also available in the dropdown list, and its type is <i>FILE</i>.')+'</p></div>';
                    step=step||'qip4';
                    checkActionqip4=function(i){
                        $('#sel'+i).addClass('highlighted');
                        return byId('req'+i).innerHTML.indexOf('title="file">'+t9n('[RU]Фото[EN]Photo')+'<')>0;
                    };
                }
                if(!reqExists(idTask,t9n('[RU]Состояние[EN]Status'))){
                    h+='<div class="qip4 qip5" id="qip5" next-step="qip6"'+isFirst(step)+'>'
                        +t9n('[RU]<p>Теперь чуть сложнее: мы захотим как-то различать выполненные, отмененные и прочие задачи. У них будет <i>Состояние</i>. Это состояние мы будем выбирать из списка возможных.</p>'
                            +'<p>Добавьте новое свойство <a class="du" onclick="if($(\'#input'+idTask+'\').is(\':visible\'))$(\'#input'+idTask+'\').val(this.innerHTML).keyup()">Состояние</a> с типом <i>SHORT</i> и поставьте галку <i>Ссылка</i>, чтобы создать справочник статусов.</p>'
                            +'<p>Кнопка <i>Создать</i> будет активна когда вы заполните эти поля верно.</p>'
                            +'[EN]<p>The next attribute is special: we\'d like to mark tasks as Completed, Cancelled, etc. The task should have some <i>Status</i>. We will choose the status from the predefined list.</p>'
                            +'<p>Add a new attribute named <a class="du" onclick="if($(\'#input'+idTask+'\').is(\':visible\'))$(\'#input'+idTask+'\').val(this.innerHTML).keyup()">Status</a> having SHORT type and check the <i>Link</i> checkbox to make it a link (i.e. reference) to the status dictionary.</p>'
                            +'<p>The <i>Add</i> button becomes active when you have these fields filled in correctly.</p>')
                            +'</div>';
                    step=step||'qip5';
                    checkActionqip5=function(i){
                        $('#sel'+i+',#ref'+i).parent().addClass('highlighted');
                        $('#newtypbtn'+i).prop('disabled',!($('#input'+i).val()===t9n('[RU]Состояние[EN]Status')&&$('#t'+i).val()==='3'&&$('#ref'+i).prop('checked')));
                        return byId('req'+i).innerHTML.indexOf('title="reference"><b>'+t9n('[RU]Состояние[EN]Status')+'<')>0;
                    };
                }
                if(!reqExists(idTask,t9n('[RU]Контакт[EN]Contact'))){
                    h+='<div class="qip61" '+isFirst(step)+'>'
                        +t9n('[RU]<p>Вы видите, что одно из свойств выделено <b>жирным</b> и имеет псевдоним в скобках. Так отображается ссылка на справочное значение: на таблицу Состояний задачи.</p>'
                            +'<p>Сама таблица&nbsp;&mdash; это одельный прямоугольник <b>Состояние</b>.</p>'
                            +'[EN]<p>You might notice that one af the attributes is marked <b>bold</b> and has an alias in brackets. This means it\'s a link: it references the record in the table of statuses.</p>'
                            +'<p>You have just created this table&nbsp;&mdash; <b>Status</b>.</p>')
                            +'<a class="btn btn-sm btn-outline-secondary" onclick="$(\'.qip61\').toggle(300)">'+t9n('[RU]Продолжить[EN]Continue')+'</a>'
                            +'</div>';
                    h+='<div class="qip61 qip62" style="display:none">'
                        +t9n('[RU]<p><b>Правило простое: связанные и подчиненные термины отображаются правее своего родителя в том же порядке, какой задан для них у родительского термина.</b></p>'
                                +'<p>Таблица Состояние находится правее таблицы Задача, потому что у задачи есть ссылка на её состояние.</p>'
                            +'[EN]<p><b>There is a simple rule: all referenced and subordinate tables are displayed on the right of their parent in the same order as these attributes listed under their parent.</b></p>'
                                +'<p>The Status table is set on the right of the Task object, which references the Status.</p>')
                            +'<a class="btn btn-sm btn-outline-secondary" onclick="$(\'.qip62\').toggle(300)">'+t9n('[RU]Продолжить[EN]Continue')+'</a>'
                            +'</div>';
                    h+='<div class="qip6 qip62" id="qip6" next-step="qip7" style="display:none">'
                        +t9n('[RU]<p>Многие задачи будут связаны с людьми&nbsp;&mdash; было бы удобно сделать в задаче ссылку на контакты этих людей.</p>'
                                +'<p>Добавьте ссылку на людей&nbsp;&mdash; назовем их <a class="du" onclick="if($(\'#input'+idTask+'\').is(\':visible\'))$(\'#input'+idTask+'\').val(this.innerHTML).keyup()">Контакт</a> (тип SHORT), точно так же, как мы это сделали с <i>состоянием</i> задачи: добавить новый термин как свойство с галкой </>Ссылка</i>.</p>'
                            +'[EN]<p>A lot of tasks would require to connect people, thus, it comes handy to link a Task to a Contact.</p>'
                                +'<p>Please add a link to a person, name it <a class="du" onclick="if($(\'#input'+idTask+'\').is(\':visible\'))$(\'#input'+idTask+'\').val(this.innerHTML).keyup()">Contact</a> (type: SHORT), the same way you just did it to create a Status link: add a new attribute as link.</p>')+'</div>';
                    step=step||'qip6';
                    checkActionqip6=function(i){
                        $('#sel'+i+',#ref'+i).parent().addClass('highlighted');
                        $('#newtypbtn'+i).prop('disabled',!($('#input'+i).val()===t9n('[RU]Контакт[EN]Contact')&&$('#t'+i).val()==='3'&&$('#ref'+i).prop('checked')));
                        if(byId('req'+i).innerHTML.indexOf('title="reference"><b>'+t9n('[RU]Контакт[EN]Contact')+'<')>0)
                            document.location.reload();
                    };
                }
                if(step!==undefined)
                    qbHead(t9n('[RU]Добавление свойств <a class="du" href="#'+idTask+'">Задачи</a>[EN]Define the <a class="du" href="#'+idTask+'">Task</a> properties'),200);
                else{ // Task attributes are defined
                    idObj=idContact=typeExists(t9n('[RU]Контакт[EN]Contact'));
                    idSocNet=typeExists(t9n('[RU]Соц.сеть[EN]Social network'));
                    if(!reqExists(idContact,t9n('[RU]Соц.сеть[EN]Social network'))||!reqExists(idContact,t9n('[RU]Категория[EN]Category'))){
                        qbHead(t9n('[RU]Добавление свойств Контакту[EN]Define the Contact properties'),chm);
                        h+='<div class="qip6 qip7 notreq2ref" id="qip7" next-step="qip8"'+isFirst(step)+'>'
                            +t9n('[RU]<p>Кликните <a class="du" href="#'+idContact+'">Контакт</a> и добавьте следующие свойства:</p>'
                                +'<ul>'
                                +'  <li><span class="pers-props">Email</span></li>'
                                +'  <li><span class="pers-props">'+t9n('[RU]Телефон[EN]Phone')+'</span></li>'
                                +'  <li><a class="du" onclick="if($(\'#input'+idContact+'\').is(\':visible\'))$(\'#input'+idContact+'\').val($(this).find(\'.pers-props\').html()).keyup()"><span class="pers-props" is-ref="true">'+t9n('[RU]Категория[EN]Category')+'</span></a> (это <b>ссылка</b> на категорию!)</li>'
                                +'  <li><a class="du" onclick="if($(\'#input'+idContact+'\').is(\':visible\'))$(\'#input'+idContact+'\').val($(this).find(\'.pers-props\').html()).keyup()"><span class="pers-props">'+t9n('[RU]Соц.сеть[EN]Social network')+'</span></a></li>'
                                +'</ul>'
                                +'<p>Какие-то из этих терминов уже есть в системе, остальные вы добавите сами.<br /><b>Внимание: здесь и далее кнопка <i>Создать</i> всегда активна, и я не буду проверять правильность введенных значений.</p>'
                                +'</div><div class="req2ref text-danger" style="display:none"><p>Вы добавили <a class="du" href="#'+idContact+'">Контакту</a> <b>свойство</b> Категория, а не <b>ссылку</b> на неё.</p>'
                                +'<p>Кликните свойство <i>Категория</i>, раскройте прямоугольник <i>Категория</i> и кликните <img class="icon8" src="https://img.icons8.com/ios/25/333333/add-link.png"> <i>Создать ссылку</i> (если там есть такая кнопка).</p>'
                                +'<p>Затем удалите у <a class="du" href="#'+idContact+'">Контакта</a> свойство <i>Категория</i> и добавьте ссылку на категорию: <nobr>--> <i>Категория</i></nobr> (ссылка отображается в списке со стрелкой).</p>'
                                +'[EN]<p>Click <a class="du" href="#'+idContact+'">Contact</a> and add the following attributes:</p>'
                                +'<ul>'
                                +'  <li><span class="pers-props">Email</span></li>'
                                +'  <li><span class="pers-props">'+t9n('[RU]Телефон[EN]Phone')+'</span></li>'
                                +'  <li><a class="du" onclick="if($(\'#input'+idContact+'\').is(\':visible\'))$(\'#input'+idContact+'\').val($(this).find(\'.pers-props\').html()).keyup()"><span class="pers-props" is-ref="true">'+t9n('[RU]Категория[EN]Category')+'</span></a> (this is a <b>link</b> to the Category!)</li>'
                                +'  <li><a class="du" onclick="if($(\'#input'+idContact+'\').is(\':visible\'))$(\'#input'+idContact+'\').val($(this).find(\'.pers-props\').html()).keyup()"><span class="pers-props">'+t9n('[RU]Соц.сеть[EN]Social network')+'</span></a></li>'
                                +'</ul>'
                                +'<p>Some of these terms already exist in the dropdown list, and you have to add the others.<br /><b>Note: from now on the <i>Add</i> button is always active, and I do not check the correctness of values. Take care!</b></p>'
                                +'</div><div class="req2ref text-danger" style="display:none"><p>You\'ve added a <b>property</b> named Category, not a <b>link</b> to it.</p>'
                                +'<p>Click the <i>Category</i> attribute, then click the <i>Category</i> box, then click <img class="icon8" src="https://img.icons8.com/ios/25/333333/add-link.png"> <i>Create link</i> (in case there is that button yet).</p>'
                                +'<p>After that, delete <i>Category</i> from <a class="du" href="#'+idContact+'">Contact</a> and add a link to Category: <nobr>--> <i>Category</i></nobr> (it start with the arrow).</p>'
                                )+'</div>';
                        step=step||'qip7';
                        checkActionqip7=function(i){
                            $('#questbox').show();
                            var j=0;
                            $('#sel'+i).parent().addClass('highlighted');
                            $('span.pers-props').each(function(){
                                if($(this).attr('is-ref')){
                                    if(normalizeType(byId('req'+i).innerHTML).indexOf(normalizeType('title="reference"><b>'+this.innerHTML+'<'))>0)
                                        j++,$(this).addClass('font-weight-bolder');
                                    if(normalizeType(byId('req'+i).innerHTML).indexOf(normalizeType('title="short">'+this.innerHTML+'<'))>0){
                                        j--;
                                        $('#id'+typeExists(t9n('[RU]Категория[EN]Category'))).addClass('highlighted');
                                        $('.req2ref').show();
                                        $('.notreq2ref').hide();
                                    }
                                    else{
                                        $('.notreq2ref').show();
                                        $('.req2ref').hide();
                                    }
                                }
                                else
                                    if(normalizeType(byId('req'+i).innerHTML).indexOf(normalizeType('title="short">'+this.innerHTML+'<'))>0)
                                        j++,$(this).addClass('font-weight-bolder');
                                    else
                                        $(this).removeClass('font-weight-bolder');
                            });
                            if(j>=4){
                                document.location.href='/'+db+'/edit_types#'+idTask;
                                document.location.reload();
                            }
                        };
                    }
                    else if(!reqExists(idSocNet,t9n('[RU]Тип ресурса[EN]Resource type'))||!reqExists(idSocNet,t9n('[RU]Примечание[EN]Notes'))){
                        idObj=idSocNet;
                        qbHead(t9n('[RU]Создание списка <i>Соц.сети</i> у[EN]Create a list of social networks of the')+' <a class="du" href="#'+typeExists(t9n('[RU]Контакт[EN]Contact'))+'">'+t9n('[RU]Контакта[EN]Contact')+'</a>',chm);
                        if(!reqExists(idSocNet,t9n('[RU]Тип ресурса[EN]Resource type'))&&!reqExists(idSocNet,t9n('[RU]Примечание[EN]Notes'))){
                            h+='<div class="qip81 pre81"'+isFirst(step)+'>'
                                +t9n('[RU]<p>У нашего контактного лица может быть несколько учетных записей в соц.сетях, поэтому мы сейчас сделаем дополнительную табличку для хранения списка ссылок на его профили в соцсетях, сайты и другие полезные ресурсы.</p>'
                                    +'<p>Для этого нам нужно добавить пару свойств к термину <i>Соц.сеть</i>.</p>'
                                    +'[EN]<p>Usually we reach our contacts using links, thus we need to store the links to their networks.</p><p>We will now create a table of links to the useful resources of our contact.<p>')
                                    +'<a class="btn btn-sm btn-outline-secondary" onclick="$(\'.qip81\').toggle(300)">'+t9n('[RU]Продолжить[EN]Continue')+'</a>'
                                    +'</div>';
                            h+='<div class="qip81 pre81 qip82" id="qip8" style="display:none">'
                                +t9n('[RU]<p>Если некое свойство само имеет свойства, то оно хранится и отображается в виде подчиненной таблицы. Кликните свойство <i class="highlighted">Соц.сеть</i> и вы перейдете к прямоугольнику его определения&nbsp;&mdash; кликните теперь его, раскрыв форму добавления свойств.</p>'
                                    +'[EN]<p>Those attributes having attributes themselves, are stored and displayed not as a single data field, but a table with records. Click the <i class="highlighted">Social network</i> attribute and you will get to the rectangle of this object definition. Click it to open the attributes control form.</p>')
                                    +'<a class="btn btn-sm btn-outline-secondary" onclick="$(\'.qip82\').toggle(300)">'+t9n('[RU]Продолжить[EN]Continue')+'</a>'
                                    +'</div>';
                            j=true
                        }
                        else
                            j=false;
                        h+='<div class="qip8 qip82 notreq2ref" id="qip8"'+(j?' style="display:none"':isFirst(step))+'>'
                            +t9n('[RU]<p>Добавьте новые свойства <i>Соц.сети</i>:<br />'
                                +' * <i><a class="du" onclick="if($(\'#input'+idSocNet+'\').is(\':visible\'))$(\'#input'+idSocNet+'\').val(this.innerHTML).keyup()">Тип ресурса</a></i> (тип SHORT, <b>ссылка</b>)'
                                +'<br /> * <i>Примечание</i> (тип MEMO, уже есть в списке)</p>'
                                +'</div><div class="req2ref text-danger" style="display:none"><p>Вы добавили <a class="du" href="#'+idSocNet+'">Соц.сети</a> <b>свойство</b> Тип ресурса, а не <b>ссылку</b> на него.</p>'
                                +'<p>Кликните свойство <i>Тип ресурса</i>, раскройте прямоугольник <i>Тип ресурса</i> и кликните <img class="icon8" src="https://img.icons8.com/ios/25/333333/add-link.png"> <i>Создать ссылку</i> (если там есть такая кнопка).</p>'
                                +'<p>Затем удалите у <a class="du" href="#'+idSocNet+'">Соц.сети</a> свойство <i>Тип ресурса</i> и добавьте ссылку на него: <nobr>--> <i>Тип ресурса</i></nobr> (ссылка отображается в списке со стрелкой).</p>'
                                +'[EN]Add the following attributes to <i>Social network</i>:<br />'
                                +' * <i><a class="du" onclick="if($(\'#input'+idSocNet+'\').is(\':visible\'))$(\'#input'+idSocNet+'\').val(this.innerHTML).keyup()">Resource type</a></i> (type: SHORT, <b>link</b>)'
                                +'<br /> * <i>Notes</i> (type: MEMO, alredy on the list)</p>'
                                +'</div><div class="req2ref text-danger" style="display:none"><p>You have added a Resource type <b>property</b> to <a class="du" href="#'+idSocNet+'">Social network</a>, not a <b>link</b> to resource.</p>'
                                +'<p>Click the <i>Resource type</i> attribute, open the <i>Resource type</i> definition rectangle and click <img class="icon8" src="https://img.icons8.com/ios/25/333333/add-link.png"> <i>Create link</i> (in case there is that button yet).</p>'
                                +'<p>After that, delete the <i>Resource type</i> attribute from <a class="du" href="#'+idSocNet+'">Social network</a> and add a link to Resource type: <nobr>--> <i>Тип ресурса</i></nobr> (it start with the arrow).</p>'
                                )+'</div>';
                        step=step||'qip8';
                        $('#id'+idSocNet).addClass('highlighted');
                        checkActionqip8=function(i){
                            if(!$('.pre81').is(':visible'))
                                if(byId('req'+i).innerHTML.indexOf('title="short">'+t9n('[RU]Тип ресурса[EN]Resource type')+'<')>0){
                                    $('#id'+typeExists(t9n('[RU]Тип ресурса[EN]Resource type'))).addClass('highlighted');
                                    $('.req2ref').show();
                                    $('.notreq2ref').hide();
                                }
                                else{
                                    $('.notreq2ref').show();
                                    $('.req2ref').hide();
                                }
                            if(byId('req'+i).innerHTML.indexOf('title="memo">'+t9n('[RU]Примечание[EN]Notes')+'<')>0
                                    &&byId('req'+i).innerHTML.indexOf('title="reference"><b>'+t9n('[RU]Тип ресурса[EN]Resource type')+'<')>0){
                                $('a[href="#'+idSocNet+'"][onclick]').removeClass('highlighted');
                                document.location.href=document.location.href.replace('ext','');
                                document.location.reload();
                            }
                            $('a[href="#'+idSocNet+'"][onclick]').addClass('highlighted');
                            return false;
                        }
                    }
                    else
                        return intApi('GET','object/'+idTask+'?JSON','Task table');
                }
                if(!curMenu('edit_types'))
                    return goMenu('edit_types',t9n('[RU]Структура[EN]Structure'));
                else
                    qbText(h);
                actTimer=setInterval(checkAction,556,step,idObj);
                break;
            
            case 'Task table':
                if(document.location.hash==='#final'){
                    qbHead(t9n('[RU]Итак, вы создали и заполнили базу данных[EN]You have just created a database and filled it in'),chm);
                    qbText('<div class="two-step"><p>'+t9n('[RU]Все ваши задачи теперь здесь.'
                            +' Вы можете фильтровать этот список по любому полю: нажмите кнопку меню <img class="icon8 icon8-0" src="https://img.icons8.com/ios/30/155724/filter.png">.'
                            +'</p><p>Правила применения фильтров описаны <a target="_blank" href="https://help.ideav.pro/#rec219525382">здесь</a>.'
                            +'[EN]Here is the set of your tasks.'
                            +' You may filter them using this menu button: <img class="icon8 icon8-0" src="https://img.icons8.com/ios/30/155724/filter.png">'
                            +'</p><p>The filtering rules are described <a target="_blank" href="https://help.ideav.pro/#rec219525382">here</a> (use the Translate option of your browser).</p>'
                            )
                        +'</div><p><a class="btn btn-sm btn-outline-secondary two-step" onclick="$(\'.two-step\').toggle(300)">'+t9n('[RU]Продолжить[EN]Continue')+'</a></p>'
                        +'<div class="two-step" style="display:none">'
                        +'<p>'+t9n('[RU]Мы потратили на изготовление этого и других уроков десятки часов, и были бы признательны вам, если бы вы уделили пару минут на регистрацию и голос за Ideav на сайте'
                            +'[EN]We have spent dozens of hours preparing this lesson and others, and we would be very grateful if you spent a couple of minutes to register and upvote Ideav at')
                        +' <a href="https://www.producthunt.com/posts/ideav" target="_blank">ProductHunt</a>.</p>'
                        +'<p>'+t9n('[RU]Кнопка голосования должна выглядеть так&nbsp;&mdash; Upvoted'
                            +'[EN]The Upvote button should look like this&nbsp;&mdash; Upvoted')+'<br /><img src="/i/upvoted.png"></p>'
                        +'<p>'+t9n('[RU]Большое спасибо! Ждем вас на следующих уроках и затем в команде Ideav.'
                            +'[EN]Thank you very much! See you at next classes and then in the Ideav team.')+'</p>'
                        +'</div>');
                    return;
                }
                if(json.object===undefined){ // No tasks registered yet
                    if(curMenu('edit_types')){
                        
                        qbHead(t9n('[RU]Поздравляю, вы создали структуру для хранения задач![EN]Wo-hoo! You\'ve just created an awesome structure to store your tasks'),chm);
                        qbText(t9n('[RU]Перед вами схематично изображены таблицы задач, контактов, соц.сетей, а также справочники состояний, категорий и типов ресурсов.'
                            +'</p><p>Теперь мы заполним все эти таблицы нашими данными.'
                            +'[EN]Here is a set of interconnected tables: tasks, contacts, resources along with the necessary dictionaries.'
                            +'</p><p>Now it\'s time to fill in the tables with data.'
                            ));
                        goMenu('dict',t9n('[RU]Таблицы[EN]Tables'));
                        document.location.hash='table'+typeExists(t9n('[RU]Задача[EN]Task'));
                        return;
                    }
                    qbHead(t9n('[RU]Заполнение таблицы задач[EN]Let us fill in the list of your tasks'),chm);
                    if(action==='object'&&id===idTask){
                        qbText(t9n('[RU]<p>Таблица задач пуста. Давайте сделаем в ней первую запись&nbsp;&mdash; нажмите кнопку (+) слева вверху и введите краткое название задачи: '
                            +'<a class="du" onclick="$(\'#t'+idTask+'\').val(this.innerHTML).focus()">Пройти урок по Структуре Ideav</a></p>'
                            +'<p>После этого нажмите кнопку <i>Добавить</i> или клавишу Enter.</p>'
                            +'[EN]The tasks table is empty. Let\'s create a new record in it: press the (+) button in the upper left corner and enter a short task description: '
                            +'<a class="du" onclick="$(\'#t'+idTask+'\').val(this.innerHTML).focus()">Complete the lesson on the Ideav data structures</a></p>'
                            +'<p>Then press the <i>Create</i> button or the Enter key.</p>'
                            ));
                        $('img[src$="plus.png"]').addClass('highlighted');
                    }
                    else if(curMenu('dict')){
                        qbText(t9n('[RU]<p>Это все зарегистрированные в системе независимые термины: те, что не являются реквизитами других терминов.</p>'
                            +'<p>Вы можете просматривать их в виде таблиц с данными: задачи, типы ресурсов, контакты и т.д. Кликните <i>Задача</i> и мы посмотрим на таблицу ваших задач.</p>'
                            +'[EN]This is the list of all independent terms: these are not an attribute of any other term.</p>'
                            +'<p>You may browse all these terms as tables of data: tasks, contacts, users, etc. Click <i>Task</i> to see the table of your tasks.</p>'
                            ));
                        $('.dict-item[onclick$="/'+idTask+'\'"]').wrap('<div/>').parent().addClass('highlighted');
                    }
                    return;
                }
                else if(action==='object'&&id===idTask&&json.reqs===undefined){
                    qbHead(t9n('[RU]Задайте свойства задачи[EN]Set the task properties'),chm);
                    qbText(t9n('[RU]Для редактирования записи в таблице задач нужно кликнуть название этой записи в первой колонке&nbsp;&mdash; <i>'+json.object[0].val+'</i>'
                        +'[EN]To edit a record in the table, click the name of this record in its leftmost column&nbsp;&mdash; <i>'+json.object[0].val+'</i>'));
                    return;
                }
                else if(json.object.length===1||!checkPHU(json.object,t9n('[RU]Самостоятельно создать свое первое приложение[EN]Create my first web-app myself'))){
                    qbHead(t9n('[RU]Вы зарегистрировали вашу задачу![EN]Your task has been created'),chm);
                    if(action==='edit_obj'&&type==idTask){
                        qbText(t9n('[RU]<p>Давайте заполним или изменим свойства: задайте дату начала выполнения, срок и <a class="du" onclick="$(\'#t'+reqExists(idTask,t9n('[RU]Описание[EN]Description'))+'\').val(\'Создать структуру задач и заполнить её данными\').focus()">описание</a>, приложите какое-нибудь фото.</p>'
                                +'[EN]Let us fill in or change its properties: set the start date, deadline, and <a class="du" onclick="$(\'#t'+reqExists(idTask,t9n('[RU]Описание[EN]Description'))+'\').val(\'Create a data structure for tsask and fill it in\').focus()">description</a>, attach a file.'));
                        $('#t'+reqExists(idTask,t9n('[RU]Срок[EN]Deadline'))+',#t'+reqExists(idTask,t9n('[RU]Дата[EN]Date'))).addClass('highlighted');
                        if($('#t'+reqExists(idTask,t9n('[RU]Состояние[EN]Status'))).val()==''){
                            qbText(t9n('[RU]Укажите <i>Состояние</i> задачи: нажмите кнопку [+] у списка состояний и введите значение <a class="du" onclick="$(\'#NEW_'+reqExists(idTask,t9n('[RU]Состояние[EN]Status'))+'\').val(this.innerHTML).focus()">Новая</a>.'
                                +'[EN]Set the <i>status</i> of the task: press the [+] button near the status dropdown list and enter <a class="du" onclick="$(\'#NEW_'+reqExists(idTask,t9n('[RU]Состояние[EN]Status'))+'\').val(this.innerHTML).focus()">New</a>.'));
                            $('#p'+reqExists(idTask,t9n('[RU]Состояние[EN]Status'))).parent().addClass('highlighted').css('margin-top', '-3px');
                        }
                        else{
                            qbText(t9n('[RU]Вы можете изменить <i>Состояние</i> задачи, добавив новое состояние в справочник кнопкой [+] у списка состояний.</p>'
                                +'[EN]You may change the Status of this task. Add a new Status to the Status dictionary using [+] button again'));
                            $('#t'+reqExists(idTask,t9n('[RU]Состояние[EN]Status'))).parent().addClass('highlighted');
                        }
                        qbText(t9n('[RU]<p>Нажмите <i>Сохранить</i>, чтобы сохранить эти изменения.</p>'
                            +'[EN]Press <i>Save</i> to save your changes.'));
                        return;
                    }
                    else if(action==='object'&&id===idTask&&!checkPHU(json.object,t9n('[RU]Самостоятельно создать свое первое приложение[EN]Create my first web-app myself'))){
                        qbHead(t9n('[RU]Вы умеете зарегистрировать задачи[EN]You can register tasks'),chm);
                        qbText(t9n('[RU]Для редактирования записи в таблице задач нужно кликнуть название этой записи в первой колонке&nbsp;&mdash; <i>'+json.object[0].val+'</i>'
                                +'</p><p>Добавьте ещё одну задачу кнопкой (+) слева вверху: '
                            +'[EN]To edit a record in the table, click the name of this record in its leftmost column&nbsp;&mdash; <i>'+json.object[0].val+'</i>'
                            +'</p><p>Create another task using the (+) button in the upper left corner: ')
                            +'<a class="du" onclick="$(\'#t'+idTask+'\').val(this.innerHTML).focus()">'+t9n('[RU]Самостоятельно создать свое первое приложение[EN]Create my first web-app myself')+'</a>');
                        $('img[src$="plus.png"]').addClass('highlighted');
                        return;
                    }
                }
                else if(action==='object'&&id===idTask&&!checkPHU(json.object,t9n('[RU]Поставить Like Интегралу[EN]Upvote Ideav at Producthunt'))){
                    qbHead(t9n('[RU]Создаем задачи[EN]Creating tasks'),chm);
                    if(search.F_I!==undefined)
                        qbText(t9n('[RU]После сохранения записи вы видите только её одну. Чтобы посмотреть полный список, очистите фильтр кнопкой меню'
                            +'[EN]When you have saved a record, you see this very record in the table&nbsp;&mdash; it\'s filtered. To see the whole list, clear the filter with')
                            +' <img class="icon8 icon8-0" src="https://img.icons8.com/ios/30/155724/clear-filters.png"></p>');
                    else{
                        qbText(t9n('[RU]Добавьте ещё одну задачу кнопкой (+) слева вверху: '
                            +'[EN]Create another task using the (+) button in the upper left corner: ')
                            +'<a class="du" onclick="$(\'#t'+idTask+'\').val(this.innerHTML).focus()">'+t9n('[RU]Поставить Like Интегралу[EN]Upvote Ideav at Producthunt')+'</a>');
                        $('img[src$="plus.png"]').addClass('highlighted');
                    }
                    return;
                }
                else if(json.object.length>1){
                    if(action==='edit_obj'&&$('#t'+idTask).val()===t9n('[RU]Самостоятельно создать свое первое приложение[EN]Create my first web-app myself')){
                        qbHead(t9n('[RU]Редактируем задачу[EN]Edit the task'),chm);
                        qbText(t9n('[RU]Задайте дату, срок и выберите состояние из списка или добавьте новое.[EN]Please set the date, and deadline. Choose the status from the list or add a new one.'));
                        qbText(t9n('[RU]Сохраните изменения.[EN]Save the changes.'));
                        $('#t'+reqExists(idTask,t9n('[RU]Срок[EN]Deadline'))+',#t'+reqExists(idTask,t9n('[RU]Дата[EN]Date'))).addClass('highlighted');
                        $('#t'+reqExists(idTask,t9n('[RU]Состояние[EN]Status'))).parent().addClass('highlighted');
                        return;
                    }
                    if(action==='edit_obj'&&$('#t'+idTask).val()===t9n('[RU]Поставить Like Интегралу[EN]Upvote Ideav at Producthunt')){
                        qbHead(t9n('[RU]Создаем задачу со ссылкой на Контакт[EN]Create a task with a link to a Contact'),chm);
                        qbText(t9n('[RU]Задайте дату, срок и состояние.[EN]Please set the date, and deadline.'));
                        qbText(t9n('[RU]Затем добавьте новый Контакт для вашей задачи кнопкой [+][EN]In addition, create a new Contact for your task using [+]')
                            +': <a class="du" onclick="$(\'#NEW_'+reqExists(idTask,t9n('[RU]Контакт[EN]Contact'))+'\').val(this.innerHTML).focus()">Ideav</a>');
                        qbText(t9n('[RU]Сохраните изменения.[EN]Save the changes.'));
                        $('#t'+reqExists(idTask,t9n('[RU]Срок[EN]Deadline'))+',#t'+reqExists(idTask,t9n('[RU]Дата[EN]Date'))).addClass('highlighted');
                        $('#t'+reqExists(idTask,t9n('[RU]Состояние[EN]Status'))).parent().addClass('highlighted');
                        $('#p'+reqExists(idTask,t9n('[RU]Контакт[EN]Contact'))).parent().addClass('highlighted').css('margin-top', '-3px');
                        return;
                    }
                    if(action==='object'&&id===idTask){
                        $('a[href*="object/'+idContact+'/"]').each(function(){
                            if(this.innerHTML==='Ideav'){
                                $(this).addClass('highlighted');
                                qbHead(t9n('[RU]Работаем со справочником Контактов[EN]Work with a Contacts dictionary'),chm);
                                qbText(t9n('[RU]Перейдите к записи о контакте, кликнув его имя, отмеченное золотым. Это ссылка на запись в таблице контактов.[EN]Go to the Contact record&nbsp;&mdash; click its name marked yellow. This is a reference to the record in the contacts table.'));
                            }
                        });
                        if($('.highlighted').length>0)
                            return;
                        qbHead(t9n('[RU]Работаем со справочником Задач[EN]Work with a Tasks dictionary'),chm);
                        qbText(t9n('[RU]Пожалуйста, добавьте контакт <i>Ideav</i> к задаче [EN]Please, add the contact <i>Ideav</i> to the task named ')
                                +'<i>'+t9n('[RU]Поставить Like Интегралу[EN]Upvote Ideav at Producthunt')+'</i>!');
                        return;
                    }
                    if(action==='object'&&id===idSocNet){
                        return intApi('GET','object/'+idSocNet+'?JSON','Resources table');;
                    }
                    if(action==='edit_obj'&&type==idSocNet){
                        qbHead(t9n('[RU]Задаём свойства ресурса[EN]Define resource properties'),chm);
                        if($('#t'+idSocNet).val().indexOf('youtube')===-1)
                            qbText(t9n('[RU]Добавьте тип ресурса &laquo;сайт&raquo;[EN]Add the resource type')+': <a class="du" onclick="$(\'#NEW_'+reqExists(idSocNet,t9n('[RU]Тип ресурса[EN]Resource type'))+'\').val(this.innerHTML).focus()">Site</a>');
                        else
                            qbText(t9n('[RU]Добавьте тип ресурса &laquo;Youtube&raquo;[EN]Add the resource type')+': <a class="du" onclick="$(\'#NEW_'+reqExists(idSocNet,t9n('[RU]Тип ресурса[EN]Resource type'))+'\').val(this.innerHTML).focus()">Youtube</a>');
                        qbText(t9n('[RU]Введите Примечание, при необходимости, и сохраните запись.[EN]Enter the notes, if any, and save the record.'));
                        $('#p'+reqExists(idSocNet,t9n('[RU]Тип ресурса[EN]Resource type'))).parent().addClass('highlighted').css('margin-top', '-3px');
                        return;
                    }
                    if(action==='object'&&id===idContact)
                        return intApi('GET','object/'+idContact+document.location.search+(document.location.search.indexOf('?')===-1?'?JSON':'&JSON'),'Contacts table');;
                }
                if(action==='edit_obj'&&type==idContact){
                    qbHead(t9n('[RU]Задаём свойства Контакта[EN]Define the Contact properties'),chm);
                    qbText(t9n('[RU]<p>Введите <a class="du" onclick="$(\'#t'+reqExists(idContact,'Email')+'\').val(\'support@'+document.location.host+'\').focus()">email</a>'
                                +' и <a class="du" onclick="$(\'#t'+reqExists(idContact,t9n('[RU]Телефон[EN]Phone'))+'\').val(\'+79859424530\').focus()">телефон</a>, также рекомендую создать или выбрать категорию клиента: Лид, Клиент, Черный список, VIP.</p>'
                                +' <p>Cохраните запись.</p>'
                            +'[EN]Enter the <a class="du" onclick="$(\'#t'+reqExists(idContact,'Email')+'\').val(\'support@'+document.location.host+'\').focus()">email</a>'
                            +' and <a class="du" onclick="$(\'#t'+reqExists(idContact,t9n('[RU]Телефон[EN]Phone'))+'\').val(\'+79859424530\').focus()">phone</a>, and you may also set a category: Lead, Client, VIP, etc.&nbsp;&mdash; create any on the fly.</p>'
                            +' <p>Save the record.</p>'));
                    $('#p'+reqExists(idSocNet,t9n('[RU]Тип ресурса[EN]Resource type'))).parent().addClass('highlighted').css('margin-top', '-3px');
                    return;
                }
                if($('#qb').html()=='')
                    qbHead(t9n('[RU]Работаем с задачами[EN]Working with your tasks'),chm);
                qbText(t9n('[RU]Перейдите в меню <i>Таблицы -> Задача</i> для продолжения урока'
                        +'[EN]Got to Tables -> Task to continue the lesson.'));
                if($('.dict-item[onclick$="/'+idTask+'\'"]').is(':visible'))
                    $('.dict-item[onclick$="/'+idTask+'\'"]').wrap('<div/>').parent().addClass('highlighted');
                else
                    $('a[href="/'+db+'/dict"]').addClass('highlighted');
                break;
                
            case 'Contacts table':
                qbHead(t9n('[RU]Таблица Контактов[EN]The Contacts dictionary'),chm);
                if(json.reqs===undefined){
                    qbText(t9n('[RU]Это список контактов, и если вы попали сюда, кликнув ссылку контакта, то он отфильтрован по этому контакту&nbsp;&mdash; всего 1 запись.[EN]This is the Contact list. When you get here using a Contact link, this is filtered by this Contact&nbsp;&mdash; a single record.'));
                    qbText(t9n('[RU]Давайте отредактируем контакт&nbsp;&mdash; кликните его имя в левой колонке.[EN]Let us edit the Contact&nbsp;&mdash; click its name in the leftmost column.'));
                }
                else{
                    qbText(t9n('[RU]У контакта есть список соц.сетей и других ресурсов. Сейчас мы заполним этот список, чтобы иметь возможность работать с этими ресурсами.[EN]The Contact has a list of resources. Let us fill in this list to be able to reach them later.'));
                    qbText(t9n('[RU]Кликните ссылку с количеством сохраненных ресурсов (в скобках) и вы попадете в связанную таблицу его ресурсов.[EN]Click the link with number of networks (in brackets) and you will get to the contact\'s table of resources.'));
                    for(i in json.reqs)
                        $('a[href$="?F_U='+i+'"]').addClass('highlighted');
                }
                break;
                
            case 'Resources table':
                qbHead(t9n('[RU]Справочник Соц.сетей[EN]Network resources list'),chm);
                $('img[src$="plus.png"]').addClass('highlighted');
                if(!checkPHU(json.object,'https://www.producthunt.com/posts/ideav'))
                    qbText(t9n('[RU]Добавьте ссылку, нажав кнопку (+)[EN]Add a link using the (+) button')+':<br />'
                        +'<a class="du" onclick="$(\'#t'+idSocNet+'\').val(this.innerHTML).focus()">https://www.producthunt.com/posts/ideav</a>');
                else if(!checkPHU(json.object,t9n('[RU]https://www.youtube.com/channel/UCwycC92C9FIJjm62aO0unIQ[EN]https://www.youtube.com/watch?v=HRDTs3JPvOc')))
                    qbText(t9n('[RU]Добавьте ещё одну ссылку, нажав кнопку (+)[EN]Add another link using the (+) button')+':<br />'
                        +'<a class="du" onclick="$(\'#t'+idSocNet+'\').val(this.innerHTML).focus()">'+t9n('[RU]https://www.youtube.com/channel/UCwycC92C9FIJjm62aO0unIQ[EN]https://www.youtube.com/watch?v=HRDTs3JPvOc')+'</a>');
                else{
                    if(search.F_I!==undefined)
                        qbText(t9n('[RU]После сохранения записи вы видите только её одну. Чтобы посмотреть все ресурсы этого контакта, очистите фильтр кнопкой меню'
                            +'[EN]When you have saved a record, you see this very record in the table&nbsp;&mdash; it\'s filtered. To see the whole list, clear the filter with')
                            +' <img class="icon8 icon8-0" src="https://img.icons8.com/ios/30/155724/clear-filters.png"></p>');
                    qbText(t9n('[RU]Добавьте любые другие ссылки нужного вам типа или нажмите [EN]Add any other link you need, and set the required type, or press')
                        +' <a href="/'+db+'/object/'+idTask+'#final">'+t9n('[RU]Продолжить[EN]Continue')+'</a>.'
                    );
                }
                break;
        }
    }
    obj.send(vars); // отправили запрос и теперь будем ждать ответ, а пока - выходим
}
function checkPHU(o,val){
    for(var i in o)
        if(o[i].val===val)
            return true;
}
$( '<style>.highlighted { border: 3px solid gold; border-radius: 15px; }'
        +'.du { border-bottom: 1px dashed; }'
    +'</style>' ).appendTo( "head" );
var idTask,idContact,idSocNet
    ,preDef={1:{t:'9',v:t9n('[RU]Дата[EN]Date')},
        2:{t:'12',v:t9n('[RU]Описание[EN]Description')},
        3:{t:'12',v:t9n('[RU]Примечание[EN]Notes')},
        4:{t:'10',v:t9n('[RU]Фото[EN]Photo')},
        5:{t:'3',v:t9n('[RU]Телефон[EN]Phone')}};
intApi('GET','edit_types?JSON','Create Task');
 
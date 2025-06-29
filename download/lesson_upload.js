$( '<style>.highlighted { border: 3px solid gold !important; border-radius: 15px; }'
        +'.du { border-bottom: 1px dashed; }'
    +'</style>' ).appendTo( "head" );
var actTimer,json,f={},step='qip1';
$(document).ready(function(){
    lessonApi('GET','dict?JSON','dict');
});
function lessonApi(m,u,b,vars,index){ // Параметры: метод, адрес, действие - ветка switch, параметры, ID целевого элемента
    vars=vars||''; // По умолчанию список параметров пуст
    var h='',i,j,obj=new XMLHttpRequest(); // Объявляем переменную под JSON и API по HTTPS
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
            case 'dict':
                for(i in json)
                    if(json[i].toUpperCase()==='MOVIE')
                        return doLesson(i);
                doLesson();
            break;
        }
    };
    obj.send(vars); // отправили запрос и теперь будем ждать ответ, а пока - выходим
}
function doLesson(movie){
    switch(document.location.pathname.replace('/'+db+'/','')){
        case 'upload':
            qbHead(t9n('[RU]Экспресс-загрузка таблиц[EN]Instant import of data'),chm,'0');
            // The movies table exists
            if(movie>0){
                // We have settings saved
                if($('#settings').find('option').length>1){
                    qbText(t9n('[RU]<p>В списке сохраненных настроек загрузки появились ваши настройки. Теперь вы можете их использовать для загрузки данных, создавать версии настроек и импортировать данные о фильмах в несколько кликов.</p>'
                            +'<p>На этом урок по эскпресс-загрузке закончен, и мы предлагаем перейти к <a class="du" onclick="stopQuest()">следующему уроку</a>.</p>'
                        +'[EN]<p>Your settings have appeared in the list of saved settings. Next time use it to upload the movies data, create their versions, and do your import in several clicks.</p>'
                            +'<p>This concludes the express-upload lesson, and we suggest moving on to <a class="du" onclick="stopQuest()">the next lesson</a>.</p>'));
                    return;
                }
                // No settings saved
                qbText('<div id="qip1" class="qip1">'
                    +t9n('[RU]<p>Теперь в списке таблиц для загрузки есть ваши новые таблицы.</p>'
                        +'<p><b>Выберите из верхнего списка <i>'+json[movie]+'</i></b>.</p>'
                        +'<p class="text-danger choose-movie" style="display:none"><b>Нажмите стрелку и выберите <i>'+json[movie]+'</i></b>.</p>'
                    +'[EN]<p>Your new tables are now in the list of tables to load.</p>'
                        +'<p><b>Select <i>'+json[movie]+'</i> from the upper dropdown list</b>.</p>'
                        +'<p class="text-danger choose-movie" style="display:none"><b>Click the arrow and choose <i>'+json[movie]+'</i></b>.</p>')
                    +'</div>'
                    );
                $('#chosenType').change(function(){
                    if(this.value===movie){
                        $('.qip1').toggle(300);
                        highlight($('#tune-btn'));
                    }
                    else{
                        $('.choose-movie').show();
                        highlight($('a[href="/'+db+'/upload"]'));
                    }
                });
                qbText('<div id="qip2" class="qip1 qip2" style="display:none">'
                    +t9n('[RU]<p>Теперь вы можете догрузить в таблицу данные, а также настроить параметры импорта, если формат файла будет меняться.</p>'
                        +'<p><b>Нажмите кнопку <i>Настроить</i></b>.</p>'
                    +'[EN]<p>Now you can upload data to the table, as well as configure import settings if the file format changes.</p>'
                        +'<p><b>Press <i>Settings</i></b>.</p>'
                    )+'</div>'
                );
                $('#tune-btn').click(function(){
                    if($('#qip2').is(':visible')){
                        $('.qip2').toggle(300);
                        setTop(0);
                    }
                });
                qbText('<div id="qip3" class="qip3 qip2" style="display:none">'
                    +t9n('[RU]<p>Здесь вы можете изменить параметры импорта: поменять поля местами, изменить типы, задать вычисление полей и прочее. Эти настройки можно сохранить для последующего использования. Вы можете сохранять различные варианты настройки на разные случаи.</p>'
                        +'<p><b>Нажмите кнопку <i>Сохранить настройку</i></b>.</p>'
                    +'[EN]<p>Here you can change the import settings: swap fields, change types, set field calculation, and more. These settings can be saved for later use. You can save different settings for different occasions.</p>'
                        +'<p><b>Press <i>Save settings</i></b>.</p>'
                    )+'</div>'
                );
                $('#save-set-btn').click(function(){
                    if($('#qip3').is(':visible')){
                        $('.qip3').toggle(300);
                        setBottom();
                        goMenu('upload');
                    }
                });
                qbText('<div id="qip4" class="qip3 qip4" style="display:none">'
                    +t9n('[RU]<p>Ваша настройка сохранена, теперь вы можете выбрать её из списка и использовать для импорта.</p>'
                    +'[EN]<p>Your setting has been saved, now you can select it from the list and use it for import.</p>'
                    )+'</div>'
                );
                return;
            }
            // The movies table does not exist yet
            qbText('<div id="qip1" next-step="qip2">'
                +t9n('[RU]<p>Вы можете выбрать любую из независимых таблиц в системе для загрузки данных или выбрать сохраненную ранее настройку импорта.</p>'
                    +'<p>Мы создадим новую таблицу, поэтому выберите из верхнего списка <i>*** Создать новую таблицу из файла ***</i>.</p>'
                +'[EN]<p>You can select any of the independent tables in the system to load data or select a previously saved import setting.</p>'
                    +'<p>We will create a new table, so select from the top list <i>*** Create new table from file ***</i>.</p>')
                +'</div>'
                );
            checkStep=function(){
                return !$('#chosenType').is(':visible');
            };
                
            f.qip2=function(){
                qbHead(t9n('[RU]Копируем исходные данные[EN]Paste the source data'),chm,'0');
                qbText('<div id="qip2" next-step="qip3">'
                    +t9n('[RU]<p>Скачайте для примера файл со списком известных фильмов: <a target="_blank" href="/download/movies.txt">txt</a> или <a target="_blank" href="/download/movies.xlsx">xls</a>.</p>'
                            +'<p>Откройте его, скопируйте всё содержимое и вставьте в это поле. Затем нажмите кнопку <i>Проверить</i>.</p>'
                        +'[EN]<p>Download the sample file of the famous movies: <a target="_blank" href="/download/movies.txt">txt</a> или <a target="_blank" href="/download/movies.xlsx">xls</a>.</p>'
                            +'<p>Open it, then copy all the content, and paste into this field. Then press the <i>Validate</i> button.</p>')
                    +'</div>'
                );
                checkStep=function(){
                    return $('#do-upload').is(':visible');
                };
            };
            
            f.qip3=function(){
                qbHead(t9n('[RU]Автоматический разбор данных[EN]Automatic data parsing'),'0','0');
                setTop(0);
                $('.stop-confirm').hide();
                qbText('<div id="qip3" class="qip3">'
                    +t9n('[RU]<p>Интеграл разобрал этот текст и показал, как он будет импортирован в систему в виде таблицы. Вы видите первые две строки, выделенные золотым: заголовок и первую запись этой таблицы.</p>'
                            +'<p>Сейчас вы можете проверить правильность распознавания заголовков полей будущей таблицы&nbsp;&mdash; изучите их внимательно.</p>'
                        +'[EN]<p>Ideav has parsed this text and showed how it will be imported into the system as a new table.<p>'
                            +'<p>You see the first two lines marked gold: the title and the first entry of that table&nbsp;&mdash; study them carefully.</p>'
                        )
                    +'<a class="btn btn-sm btn-outline-secondary mb-2" onclick="nextTab(this);f.qip31()">'+t9n('[RU]Продолжить[EN]Continue')+'</a>'
                    +'</div>'
                );
                qbText('<div id="qip31" class="qip3 qip31" style="display:none">'
                    +t9n('[RU]<p>Ниже вы можете настроить импорт&nbsp;&mdash; переименовать поля, задать им другой тип, сделать их списочными значениями, поменять их местами, пропустить ненужные колонки, вычислить значения полей.</p>'
                            +'<p>Например, нам не понадобится <i>Rank</i>&nbsp;&mdash; номер по порядку в исходном файле. <b>Снимите галку в колонке <i>Rank</i>, и она не будет импортирована</b>.</p>'
                        +'[EN]<p>Below you can set up import&nbsp;&mdash; rename fields, set them to a different type, make them list values, swap them, skip unnecessary columns, calculate field values.</p>'
                            +'<p>For example, we don\'t need <i>Rank</i>&nbsp;&mdash; the record order in the source file. <b>Uncheck the <i>Rank</i> column and it will not be imported</b>.</p>'
                        )
                    +'</div>'
                );
                f.qip31=function(){
                    highlight($('input[value=Rank]').parent());
                    $('input[value=Rank]').parent().find('input[type=checkbox]').click(function(){
                        if(!this.checked&&$('#qip31').is(':visible')){
                            $('.qip31').toggle(300);
                            f.qip32();
                            this.disabled=true;
                        }
                    });
                };
                qbText('<div id="qip32" class="qip32 qip31" style="display:none">'
                    +t9n('[RU]<p>Теперь давайте переименуем колонку <i>Title</i>&nbsp;&mdash; впишите вместо <i>Title</i> слово <i>Movie</i> и нажмите Enter.</p>'
                            +'<p id="mov" class="text-danger font-weight-bold" style="display:none">Введите название колонки&nbsp;&mdash; <a class="du" onclick="$(\'.movie-title\').val(this.innerHTML).change().focus()">Movie</a>.</p>'
                        +'[EN]<p>Now let\'s rename the <i>Title</i> column&nbsp;&mdash; replace <i>Title</i> with the word <i>Movie</i> and press Enter.</p>'
                            +'<p id="mov" class="text-danger font-weight-bold" style="display:none">Enter the column name exactly: <a class="du" onclick="$(\'.movie-title\').val(this.innerHTML).change().focus()">Movie</a>.</p>'
                        )
                    +'</div>'
                );
                f.qip32=function(){
                    highlight($('input[value=Title]'));
                    $('input[value=Title]').addClass('movie-title')
                    $('.movie-title').change(function(){
                        if(this.value.toUpperCase().trim()==='MOVIE'&&$('#qip32').is(':visible')){
                            this.value=this.value.trim();
                            $('.qip32').toggle(300);
                            $('#mov').hide();
                            f.qip33();
                        }
                        else
                            $('#mov').show();
                    });
                };
                qbText('<div id="qip33" class="qip32 qip33" style="display:none">'
                    +t9n('[RU]<p>Будет удобно сделать жанр (Genre) и режиссера (Director) фильма справочными значениями, чтобы при добавлении фильмов выбирать их из списка.</p>'
                            +'<p><b>Нажмите иконку ссылки <img src="https://img.icons8.com/ios/22/155724/link.png"> возле <i>Genre</i> и <i>Director</i>, чтобы обозначить эти поля как справочные</b>.</p>'
                        +'[EN]<p>It will be convenient to make the Genre and Director of the movie as reference values, so that we select those from the list when adding movies.</p>'
                            +'<p><b>Click the link icon <img src="https://img.icons8.com/ios/22/155724/link.png"> near <i>Genre</i> and <i>Director</i> to mark these fields as reference</b>.</p>'
                        )
                    +'</div>'
                );
                f.qip33=function(){
                    highlight($('input[value=Genre],input[value=Director]').parent());
                    $('.icon8').click(function(){
                        if($('.is-link').length>1&&$('#qip33').is(':visible')){
                            $('.qip33').toggle(300);
                            f.qip34();
                        }
                    });
                };
                qbText('<div id="qip34" class="qip34 qip33" style="display:none">'
                    +t9n('[RU]<p>Поле описания фильма&nbsp;&mdash; Description&nbsp;&mdash; будет удобнее редактировать в многострочном поле ввода, а не одной строкой.</p>'
                            +'<p><b>Измените тип этого поля с <i>chars</i> на <i>memo</i>, чтобы он отображался так на форме редактирования фильма</b>.</p>'
                        +'[EN]<p>The film Description field will be more convenient to edit in a multi-line input field, not in one line.</p>'
                            +'<p><b>Please change the type of this field from <i>chars</i> to <i>memo</i> to make it look like as a text box in the film edit form</b>.</p>'
                        )
                    +'</div>'
                );
                f.qip34=function(){
                    highlight($('input[value=Description]').parent());
                    $('input[value=Description]').parent().find('select').change(function(){
                        if(parseInt(this.value)===12&&$('#qip34').is(':visible')){
                            $('.qip34').toggle(300);
                            f.qip35();
                        }
                    });
                };
                qbText('<div id="qip35" class="qip34 qip35" style="display:none">'
                    +t9n('[RU]<p>Вы внесли изменения в настройки и теперь следует перезапустить автоматический разбор файла, чтобы применить эти настройки.</p>'
                            +'<p><b>Нажмите синюю кнопку <i>Проверить</i></b>.</p>'
                        +'[EN]<p>You have made changes to the settings and now you must restart the automatic parsing of the file in order to apply these settings.</p>'
                            +'<p><b>Please press the blue <i>Validate</i> button</b>.</p>'
                        )
                    +'</div>'
                );
                f.qip35=function(){
                    highlight($('#try'));
                    $('#try').click(function(){
                        if($('#qip35').is(':visible')){
                            $('.qip35').toggle(300);
                            f.qip36();
                        }
                    });
                };
                qbText('<div id="qip36" class="qip36 qip35" style="display:none">'
                    +t9n('[RU]<p>Внизу страницы оторажена вся <a href="#page">таблица</a>, которая будет создана: имена колонок с указанием общего количества строк. Изучите таблицу, чтобы  убедиться, что данные распознаны верно, а Genre и Director&nbsp;&mdash; справочные значения (со значками ссылок).</p>'
                            +'<p><b>Нажмите кнопку <i>Статистика</i> для просмотра сводной информации о загружаемых данных</b>.</p>'
                        +'[EN]<p>You have made changes to the settings and now you must restart the automatic parsing of the file in order to apply these settings.</p>'
                            +'<p><b>Please press the blue <i>Validate</i> button</b>.</p>'
                        )
                    +'</div>'
                );
                f.qip36=function(){
                    highlight($('#resume'));
                    $('#show-stats').click(function(){
                        if($('#qip36').is(':visible')){
                            $('.qip36').toggle(300);
                            f.qip37();
                        }
                    });
                };
                qbText('<div id="qip37" class="qip36 qip37" style="display:none">'
                    +t9n('[RU]<p>Вы можете проверить правильность разбора данных по этой таблице: здесь есть минимальные, максимальные, суммарные и средние значения полей, показано количество пустых ячеек. Это бывает удобно, например, для сверки с исходным Excel-файлом, где вы можете сверить суммы по колонкам.</p>'
                            +'<p>Когда всё будет проверено, <b>нажмите кнопку <i>Загрузить</i> и подтвердите загрузку</b>.</p>'
                        +'[EN]<p>You can check the correctness of data parsing in this table: there are minimum, maximum, total and average field values, the number of empty cells is shown. This can be convenient, for example, for reconciliation with the original Excel file, where you can reconcile sums by columns.</p>'
                            +'<p>When everything is checked, <b>click the <i>Upload</i> button and confirm the upload</b>.</p>'
                        )
                    +'</div>'
                );
                f.qip37=function(){
                    highlight($('#stats'));
                    $('.btn-warning.confirm').click(function(){
                        if($('#qip37').is(':visible')){
                            $('.qip37').toggle(300);
                            highlight($('#progress,#log'));
                            setBottom();
                        }
                    });
                };
                qbText('<div id="qip38" class="qip38 qip37" style="display:none">'
                    +t9n('[RU]<p>Интеграл отобразит в журнале, какие таблицы и поля были созданы в процессе импорта, затем загрузит данные и заполнит связанные справочники.</p>'
                            +'<p>Загрузка идет со скоростью от 500 до 3000 записей в секунду, и когда она закончится, <b>перейдите в меню <i>Таблицы</i></b>, чтобы увидеть ваши новые таблицы.</p>'
                        +'[EN]<p>The integral will display in the log which tables and fields were created during the import process, then it will load the data and fill in the related dictionaries.</p>'
                            +'<p>The upload rate is usually 500 to 3000 records per second, and when it is done, <b>go to the <i>Tables</i></b> menu to see your new tables.</p>'
                        )
                    +'</div>'
                );
                $('#sample').addClass('highlighted');
                return;
            };
            actTimer=setInterval(checkStepAction,556);
            break;
        case 'object/'+movie:
        case 'object/'+movie+'/':
            qbHead(t9n('[RU]Таблица фильмов[EN]Movies table'),chm);
            if(search.order_val>0&&search.desc===undefined)
                qbText(t9n('[RU]Кликните имя колонки ещё раз, чтобы отсортировать её по убыванию её значений.'
                        +'[EN]Click the column name again to sort it in descending order.'));
            else if(search.order_val>0){
                qbText('<p>'+t9n('[RU]Таблица отсортирована по убыванию значений поля '
                        +'[EN]Table sorted in descending order of values of ')+$('a[colid='+search.order_val+']').html().substring(2)+'.</p>'
                    +'<p>'+t9n('[RU]Если вам понадобится добавить колонки в эту таблицу, то вы сможете сделать это в меню Структура'
                        +'[EN]If you need to add columns to this table, you can do so from the Structure menu.')+'.</p>'
                );
                goMenu('edit_types');
            }
            else
                qbText(t9n('[RU]<p>Поздравляем! Вы умеете импортировать данные в Интеграл, и вы видите, что делается это очень быстро и просто.</p>'
                        +'<p>Это импортированные вами данные: здесь их можно фильтровать и сортировать по любому полю. Вы можете редактировать эти записи, нажав на значение в самой левой колонке.</p>'
                        +'<p>Отсортируйте таблицу по полю Year&nbsp;&mdash; нажмите его название.</p>'
                    +'[EN]<p>Congratulations! You have learned how to import data into Ideav, and you do it very quickly and easy.</p>'
                        +'<p>This is the data you imported: here you can filter and sort it by any field. You can edit these entries by clicking on the value in the leftmost column.</p>'
                        +'<p>Sort the table by the Year field&nbsp;&mdash; click its name.</p>'
                ));
            break;
        case 'edit_types':
            if(movie>0){
                qbHead(t9n('[RU]Редактор структуры данных[EN]Table structure editor'),chm);
                qbText(t9n('[RU]Если вам понадобится изменить состав, типы, порядок, имена полей, то вы можете сделать это здесь. Таблица фильмов схематично изображена с двумя справочниками режиссеров и жанров&nbsp;&mdash; кликните'
                        +'[EN]If you need to change the composition, types, order, field names, then you can do it here. Movie table schematically depicted with two directors and genre dictionaries&nbsp;&mdash; click ')
                        +' <a class="du" href="#'+movie+'">'+json[movie]+'</a>.'
                );
                goMenu('upload');
            }
            else
                defaultMsg();
            break;
        case 'dict':
            if(movie>0){
                qbHead(t9n('[RU]Таблицы Интеграла[EN]Ideav tables'),chm);
                qbText(t9n('[RU]Здесь вы видите импортированные вами таблицы фильмов, жанров и режиссеров&nbsp;&mdash; откройте таблицу режиссеров, а потом, вернувшись сюда, таблицу фильмов.'
                        +'[EN]Here you see the tables of movies, genres and directors that you imported&nbsp;&mdash; open the table of directors, and then, returning here, the table of movies.')
                );
                h=['MOVIE','GENRE','DIRECTOR'];
                $('.dict-item').each(function(){
                    if(h.indexOf(this.innerHTML.toUpperCase())!==-1)
                        $(this).addClass('highlighted');
                });
            }
            else
                defaultMsg();
            break;
        default:
            defaultMsg();
            break;
    }
}
function defaultMsg(){
    if(document.location.pathname.indexOf('/'+db+'/object/')===0&&$('a[colid="val"]').html().toUpperCase()==='DIRECTOR'){
        qbHead(t9n('[RU]Справочник режиссеров[EN]Directors list'),chm);
        qbText(t9n('[RU]Это список всех режиссеров фильмов&nbsp;&mdash; Интеграл заполнил справочник именами из загруженного списка.'
                    +'[EN]This is a list of all film directors&nbsp;&mdash; Ideav filled the directory with the names from the uploaded list.')
            );
        goMenu('dict');
        return;
    }
    qbHead(t9n('[RU]Быстрый импорт структур и данных[EN]Instant data and structure import'),chm);
    qbText(t9n('[RU]В этом уроке мы загрузим данные из текстового файла или таблицы Excel, просто скопировав его содержимое в Интеграл.'
                +'[EN]In this tutorial, we will load data from a text file or an Excel spreadsheet by simply copying its contents into Ideav.')
        );
    goMenu('upload');
}
function highlight(el){
    $('.highlighted').removeClass('highlighted');
    $(el).addClass('highlighted');
}
function checkStepAction(){
    console.log(step);
    try{
        if(!window.checkStep())
            return;
    }
    catch(e){
        return;
    }
    clearInterval(actTimer);
    if($('#'+step).attr('next-step')!==undefined){
        step=$('#'+step).attr('next-step');
        actTimer=setInterval(checkStepAction,556);
        f[step]();
    }
}
function nextTab(el){
    $('.'+$(el).parent().attr('id')).toggle(300);
}
function highlightBtn(s,add){
    if(!add)
        $('.highlighted').removeClass('highlighted');
    $('img[src$="'+s+'"]').addClass('highlighted');
}
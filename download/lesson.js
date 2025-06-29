function normalizeType(v){
    return v.toLowerCase().replace(/[^a-zа-я0-9]/gm,'');
}
function typeExists(v){
    v=normalizeType(v);
    for(var i in types)
        if(normalizeType(types[i].v)===v)
            return i;
}
function reqExists(t,v){
    v=normalizeType(v);
    for(var i in reqs[t])
        if(reqs[t][i].t)
            if(normalizeType(types[reqs[t][i].t].v)===v)
                return reqs[t][i].i;
}
function getMenuName(menuTag){
    for(var i in menu)
        if(menu[i].href===menuTag)
            return i;
}
function goMenu(menuTag){
    qbText('<div>'+t9n('[RU]Пройдите в меню <i>'+menu[getMenuName(menuTag)].name+'</i>, чтобы продолжить урок[EN]Go to the <i>'+menu[getMenuName(menuTag)].name+'</i> menu to proceed')+'.</div>');
    highlightMenu(menuTag);
}
function checkAction(step,param){
    console.log(step+' '+'checkAction'+step+'('+param+')');
    try{
        if(!window['checkAction'+step](param))
            return;
    }
    catch(e){
        return;
    }
    $('.'+step).toggle();
    clearInterval(actTimer);
    if($('#'+step).attr('next-step')!==undefined)
        actTimer=setInterval(checkAction,556,$('#'+step).attr('next-step'),param);
}
function isFirst(s){
    return s===undefined?'':' style="display:none"';
}
function highlightMenu(m){
    $('.highlighted').removeClass('highlighted');
    $('a[href="/'+db+'/'+m+'"]').addClass('highlighted');
    if(!$('a[href="/'+db+'/'+m+'"]').is(":visible"))
        $('.expand-menu').addClass('highlighted');
}
function curMenu(m){
    return document.location.pathname.indexOf(db+'/'+m)===1;
}
function stopQuest(){
    document.cookie='_qip=;max-age=0;Path=/'+db;
    document.location.href='/'+db;
}
function setTop(t){
    $('#questbox').css('top',window.scrollY+(qby=t)+'px');
}
function fontSize(){
    fontS=fontS^1;
    $('#questbox').css('font-size',fontS===1?'smaller':'');
    document.cookie='_fontsize='+fontS+';max-age=31536000;Path=/'+db;
}
function setWidth(){
    if(lastLeft===undefined){
        lastLeft=$('#questbox').css('left');
        $('#questbox').css('left',0);
    }
    else{
        $('#questbox').css('left',lastLeft);
        lastLeft=undefined;
    }
}
function setBottom(){
    $('#questbox').css('top',window.scrollY+(qby=ch-$('#questbox').outerHeight())+'px');
}
function qbHead(t,top,left){
    if(top!==undefined)
        setTop(top);
    $('#qb').html('<p style="margin-right:63px;"><b>'+t+'<b></p>');
    $('#questbox').css('left',(left||Math.max(120,cwm))+'px').show();
}
function qbText(t,top,left){
    if(top!==undefined)
        setTop(top);
    $('#qb').append(t.indexOf('<p>')===-1?'<p>'+t+'</p>':t);
}
function scrollQb(e){
    if(window.scrollY===0)
        return;
    $('#questbox').css('top',(window.scrollY+qby)+'px');
    clearInterval(scrollTimer);
}
$( '<style>.highlighted { border: 3px solid gold; border-radius: 15px; }'
        +'.du { border-bottom: 1px dashed; }'
    +'</style>' ).appendTo( "head" );
// Initialize the Quest box
var fontS=getCookie('_fontsize')=='1'?1:0;
var ch=document.documentElement.clientHeight,cw=document.documentElement.clientWidth
    ,lastLeft,qby=0,qbx,chm=Math.round(ch/2*0.8),cwm=Math.round(cw/2*0.8)
    ,qb='<div id="questbox" style="position: absolute; z-index:1100;'+(fontS===1?' font-size:smaller;':'')+' display:none;">'
        +'<div class="alert alert-success shadow" id="qbHandle">'
        +'<div  style="position: absolute; right: 0px;">'
        +'<img class="icon8 font-size font-increase" src="https://img.icons8.com/ios/25/333333/type.png" onclick="fontSize()">'
        +' <img class="icon8" src="https://img.icons8.com/ios/25/333333/width.png" onclick="setWidth()">'
        +' <img class="icon8" src="https://img.icons8.com/ios/25/333333/up.png" onclick="setTop(0)">'
        +'</div><div id="qb"></div>'
        +'<img class="icon8" src="https://img.icons8.com/ios/25/333333/down.png" onclick="setBottom()" style="position: absolute; z-index: 2;  right: 0px; bottom: 0px;">'
        +'<p class="stop-confirm pt-2"><font size="-1" color="#1a6d2d"><a onclick="$(\'.stop-confirm\').toggle(300)">'+t9n('[RU]Остановить урок[EN]Break the lesson')+'</a></font></p>'
        +'<p class="stop-confirm" style="display:none"><a class="btn btn-sm btn-outline-secondary" onclick="$(\'.stop-confirm\').toggle(300)">'+t9n('[RU]Продолжить[EN]Continue')+'</a>'
        +'&nbsp; &nbsp; <a class="btn btn-sm btn-outline-secondary" onclick="stopQuest()">'+t9n('[RU]Остановить[EN]Stop')+'</a>'
//        +'&nbsp; &nbsp; <a class="btn btn-sm btn-outline-secondary" onclick="resetQuest()">Начать заново</a>'
        +'</p></div>'
        +'</div>'
    ,scrollTimer,actTimer
    ,types={},reqs={};
$(document).ready(function() {
    $('body').append(qb);
    $("#questbox").draggable({
        handle:"#qbHandle",
        stop: function() {
                console.log(window.scrollY+' '+qby+' '+$('#questbox').css('top'));
                qby=$('#questbox').css('top').replace('px','')-window.scrollY;
            }
    });
    scrollTimer=setInterval(scrollQb,300);
    window.addEventListener('scroll', function(e) {
        $('#questbox').css('top',(window.scrollY+qby)+'px');
    });
    var script = document.createElement("script");
    script.src = '/download/lesson_'+_qip+'.js?'+Math.random();
    document.head.appendChild(script);
});

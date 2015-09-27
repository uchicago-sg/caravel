var mq = window.matchMedia('all and (max-width: 750px)');
if(mq.matches) {
    // the width of browser is more then 700px
} else {
    // the width of browser is less then 700px
    $( ".row-eq-height").remove();
}


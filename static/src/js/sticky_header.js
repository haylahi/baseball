$(document).ready(function () {

    var stickyHeaderTop = $('#header_top_bar').offset().top;


    $(window).scroll(function() {
    if ($(this).scrollTop() > stickyHeaderTop){  
        $('#header_top_bar').addClass("sticky");
        $('#header_top_bar_alias').addClass("sticky");
        $('#logo_header').addClass("sticky");
      }
      else{
        $('#header_top_bar').removeClass("sticky");
        $('#header_top_bar_alias').removeClass("sticky");
        $('#logo_header').removeClass("sticky");
      }
    });
});



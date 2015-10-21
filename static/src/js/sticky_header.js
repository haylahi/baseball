$(document).ready(function () {

    var stickyHeaderTop = $('#header_top_bar,#header_top_bar_single').offset().top;
    var stickyLogoTop = $('#logo_header').offset().top;


    $(window).scroll(function() {
    if ($(this).scrollTop() > stickyHeaderTop){  
        $('#header_top_bar').addClass("sticky");
        $('#header_top_bar_alias').addClass("sticky");        
        $('#header_top_bar_single').addClass("sticky");
        $('#header_top_bar_alias_single').addClass("sticky");
      }
      else{
        $('#header_top_bar').removeClass("sticky");
        $('#header_top_bar_alias').removeClass("sticky");
        $('#header_top_bar_single').removeClass("sticky");
        $('#header_top_bar_alias_single').removeClass("sticky");
      }
      
    if ($(this).scrollTop() > stickyLogoTop){  
        $('#logo_header').addClass("sticky");
      }
      else{
        $('#logo_header').removeClass("sticky");
      }
    });
});



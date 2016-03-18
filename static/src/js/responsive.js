$(document).ready(function () {
  $(function () {
    $('.footable').footable();
  });

      if ($( window ).width() < 768){  
        $('.panel').addClass("panel-old").removeClass("panel");
        $('.panel-title').addClass("panel-title-old").removeClass("panel-title");        
        $('.panel-body').addClass("panel-body-old").removeClass("panel-body");
        $('.panel-heading').addClass("panel-heading-old").removeClass("panel-heading");
        $('.panel-default').addClass("panel-default-old").removeClass("panel-default");
      }
      else{
        $('.panel-old').addClass("panel").removeClass("panel-old");
        $('.panel-title-old').addClass("panel-title").removeClass("panel-title-old");        
        $('.panel-body-old').addClass("panel-body").removeClass("panel-body-old");
        $('.panel-heading-old').addClass("panel-heading").removeClass("panel-heading-old");
        $('.panel-default-old').addClass("panel-default").removeClass("panel-default-old");
      }

  $('[data-toggle=offcanvas]').click(function() {
    $('.row-offcanvas-right').toggleClass('active', 200);
  });

  $('.dropdown-toggle-menu').click(function() {
    var id = $(this).attr('id')
    $('[parent_id='+id+']').toggleClass('hidden', 200);
  });

});

$(document).ready(function () {
    $(window).resize(function() {
      if ($( window ).width() < 768){  
        $('.panel').addClass("panel-old").removeClass("panel");
        $('.panel-title').addClass("panel-title-old").removeClass("panel-title");        
        $('.panel-body').addClass("panel-body-old").removeClass("panel-body");
        $('.panel-heading').addClass("panel-heading-old").removeClass("panel-heading");
        $('.panel-default').addClass("panel-default-old").removeClass("panel-default");
      }
      else{
        $('.panel-old').addClass("panel").removeClass("panel-old");
        $('.panel-title-old').addClass("panel-title").removeClass("panel-title-old");        
        $('.panel-body-old').addClass("panel-body").removeClass("panel-body-old");
        $('.panel-heading-old').addClass("panel-heading").removeClass("panel-heading-old");
        $('.panel-default-old').addClass("panel-default").removeClass("panel-default-old");
      }
    });
});



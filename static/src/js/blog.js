$(document).ready(function() {
    if ($('.website_blog').length) {
        function page_transist(event) {
            event.preventDefault();
            newLocation = $('.js_next')[0].href;
            window.location.href = newLocation;
        }

        $('.blog_footer').on('click',page_transist);
    }

});



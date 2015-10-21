$(document).ready(function () {


    $('.js_game_score')
        .off('click')
        .click(function (event) {
            var item = this
            var game_id = parseInt(this.attributes.id.value);
            openerp.jsonRpc("/game/score", 'call', {
                    'game_id': game_id,
                    kwargs: {
                       context: openerp.website.get_context()
                    },
                }).then(function (value) {
                    if (value.scoring== true){
                        $(item).replaceWith(value.scorer);
                    };
                });
            return false;
        });

    $('.js_game_umpire')
        .off('click')
        .click(function (event) {
            var item = this
            var game_id = parseInt(this.attributes.id.value);
            openerp.jsonRpc("/game/umpire", 'call', {
                    'game_id': game_id,
                    kwargs: {
                       context: openerp.website.get_context()
                    },
                }).then(function (value) {
                    if (value.umpiring== true){
                        $(item).replaceWith(value.umpire);
                    };
                });
            return false;
        });

});



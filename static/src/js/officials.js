odoo.define('website.editor', function (require) {
'use strict';

var ajax = require('web.ajax');
var website = require('website.website');

$(document).ready(function () {


    $('.js_game_score')
        .off('click')
        .click(function (event) {
            var item = this
            var game_id = parseInt(this.attributes.id.value);
            ajax.jsonRpc("/game/score", 'call', {
                    'game_id': game_id,
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
            ajax.jsonRpc("/game/umpire", 'call', {
                    'game_id': game_id,
                }).then(function (value) {
                    if (value.umpiring== true){
                        $(item).replaceWith(value.umpire);
                    };
                });
            return false;
        });

});
});



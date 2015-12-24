odoo.define('website.editor', function (require) {
'use strict';

var ajax = require('web.ajax');
var website = require('website.website');


$(document).ready(function () {


    $('.js_player')
        .off('click')
        .click(function (event) {
            var player_id = parseInt(this.attributes.id.value);
            ajax.jsonRpc("/player", 'call', {
                    'player_id': player_id,
                }).then(function (modal) {
                    var $modal = $(modal);
                    $modal.modal()
                        .on('hidden.bs.modal', function () {
                            $(this).remove();
                        });
                });
            return false;
        });

    $('.js_game')
        .off('click')
        .click(function (event) {
            var game_id = parseInt(this.attributes.id.value);
            ajax.jsonRpc("/game", 'call', {
                    'game_id': game_id,
                }).then(function (modal) {
                    var $modal = $(modal);
                    $modal.modal()
                        .on('hidden.bs.modal', function () {
                            $(this).remove();
                        });
                });
            return false;
        });

    $('.js_game_attend')
        .off('click')
        .click(function (event) {
            var item = this
            var game_id = parseInt(this.attributes.id.value);
            ajax.jsonRpc("/game/attend", 'call', {
                    'game_id': game_id,
                }).then(function (value) {
                    if (value.attending== true){
                        $(item).parent().find('.js_game_absent').removeClass( "text-danger");
                        $(item).addClass( "text-success" );
                    };
                });
            return false;
        });

    $('.js_game_absent')
        .off('click')
        .click(function (event) {
            var item = this
            var game_id = parseInt(this.attributes.id.value);
            ajax.jsonRpc("/game/absent", 'call', {
                    'game_id': game_id,
                }).then(function (value) {
                    if (value.attending == false){
                        $(item).parent().find('.js_game_attend').removeClass( "text-success");
                        $(item).addClass( "text-danger" );
                    };
                });
            return false;
        });
});

});



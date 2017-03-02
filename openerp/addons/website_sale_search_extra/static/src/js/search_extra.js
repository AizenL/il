

odoo.define('website_sale_search_extra.search_dynamic', function (require) {
'use strict';

    var ajax = require('web.ajax');
    var animation = require('web_editor.snippets.animation');

    animation.registry.search_dynamic = animation.Class.extend({
        selector: ".input-group",
        start: function (editable_mode) {
            var self = this;
            this.$target.find(".oe_search_box").on("input", function(e) {
                if (this.value.length > 3) {
                    ajax.jsonRpc("/shop/search", "call", {
                        search: this.value
                    }).then(function(data) {
                        self.render(data);
                    });
                }
            });
        },
        render: function (data) {
            console.log("data", data);
            //this.$target.find(".query-result").text(data["query"]);
        }
    });

});
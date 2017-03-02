(function () {
    'use strict';
    var website = openerp.website;

        website.snippet.animationRegistry.search_autocomplete = website.snippet.Animation.extend({
        selector: ".search-query",



        start : function() {

           var self = this;
           var html = document.documentElement;
           var lang=html.getAttribute('lang').replace('-', '_');
           this.$target.attr("autocomplete","off");
           this.$target.parent().addClass("typeahead-container");

           this.$target.typeahead({
                minLength: 1,
                maxItem: 15,
                groupMaxItem: 10,
                dynamic:true,
                delay: 500,
                order:"asc",
/*                group: ["category", "{{group}}"],
                display: ["product", "category"],*/
/*                template: '<span>' +
                          '<span>{{product}}</span>' +
                          '</span>',*/
/*                source:{
                        product:{
                               url: [{
                                         type : "GET",
                                          url : "/search/autocomplete?lang="+lang,
                                          data : { query : "{{query}}"}
                                     },
                                     "data.product"]
                          },
                        },*/
                source: {
                            itemlist: {
                                href: "{{ItemLink}}",
                                path: 'data.Groups',
                                ajax: function (term) {
                                    return {
                                        url: "/search/autocomplete?lang="+lang,
                                        dataType: "jsonp",
                                        data: {
                                            term: "{{query}}"
                                        }
                                    }
                                }
                            },
                        },                        
              });
        },
    });

})();

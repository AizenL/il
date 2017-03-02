
$(document).ready(function () {
    $.widget( "custom.catcomplete", $.ui.autocomplete, {
        _create: function() {
          this._super();
          this.widget().menu( "option", "items", "> :not(.ui-autocomplete-category)" );
        },
        _renderMenu: function( ul, items ) {
          var that = this,
            currentCategory = "";
          $.each( items, function( index, item ) {
/*            var li;
            if ( item.category != currentCategory ) {
              ul.append( "<li class='ui-autocomplete-category'>" + item.category + "</li>" );
              currentCategory = item.category;
            } */
            li = that._renderItemData( ul, item );
            if ( item.category ) {
              li.attr("id",item.category, "aria-label", item.category + " : " + item.label );
            }
          });
        }
      });
    
	$('.oe_website_sale').each(function () {
	    var oe_website_sale = this;
	    var availableTags = [];
	    

	    
	    $(oe_website_sale).on('keyup', "input[name='search']", function () {
		   
	    	var dInput = $('input:text[name=search]').val();
		   
		    openerp.jsonRpc("/shop/get_products", 'call', {'key_in_data':dInput})
			.then(function (data) {
				availableTags = data
			});
		    console.log(availableTags);

		      	    	
	    	console.log(dInput)
	    	$(oe_website_sale).find("input[name='search']").catcomplete({	    		
			
	    		source: availableTags,

				
			});
	    });
	    $(oe_website_sale).find("input[name='search']").keyup();
	});
});

/*

$(document).ready(function () {
	$('.oe_website_sale').each(function () {
	    var oe_website_sale = this;
	    var availableTags = [];
	    openerp.jsonRpc("/shop/get_products", 'call', {})
		.then(function (data) {
			availableTags = data
		});
	    $(oe_website_sale).on('keyup', "input[name='search']", function () {
	    	$(oe_website_sale).find("input[name='search']").autocomplete({	    		
				source: availableTags,
				selectFirst: true, //here
				minLength: 2,
				max:10
				
			});
	    });
	    $(oe_website_sale).find("input[name='search']").keyup();
	});
});
*/

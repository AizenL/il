
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
	    
	    var delay = (function() {
	        var timer = 0;
	        return function(callback, ms) {
	            clearTimeout(timer);
	            timer = setTimeout(callback, ms);
	        };
	    })();  
	    
	    $(oe_website_sale).on('keyup', "#search", function () {
	    	 var dInput = $('#search').val();
	    	 
	    	 	openerp.jsonRpc("/shop/get_products", 'call', {'key_in_data':dInput})
				.then(function (data) {
					availableTags = data
				});
	    	$(oe_website_sale).find("#search").catcomplete({	    		

	    		source: availableTags,
	    		minLength: 2,
	    		delay: 500,
	            autoFocus: true,	    		
	            selectFirst: true, //here
	    		select: function(event, ui) {
	    			
	    	            var selectedObj = ui.item;
	    	            $('#search').val(dInput);
	    	            $('#categ_id').val(selectedObj.category);
	    	            console.log(selectedObj.label);
	    	            $search_value = selectedObj.label;
	    	            parent_cat = selectedObj.parent_name.replace(/\s+/g, '-').toLowerCase();
	    	            
	    	            
	    	            $remove_in = $search_value.replace(/^([^ ]+ ){2}/, '').toLowerCase();
	    	            $trim_string = $remove_in.trim();
	    	           
	    	            sreplace_space = $trim_string.replace(/\s+/g, '-');
	    	            
	    	            $query_string = parent_cat+'-'+sreplace_space+'-'+selectedObj.category+'?search='+dInput;
	    	            
	    	            console.log($query_string)
	    	            
	    	            $("#ilsearch").attr("action", "/shop/category/"+$query_string);
	    	            $("#ilsearch").submit();
	    	            return false;
	    	        }				
			});
	    	 
	    	 
	   /* 	 $(oe_website_sale).find("#search").catcomplete({
	    	      source: function( request, response ) {
	    	    	  lastXhr = openerp.jsonRpc("/shop/get_products", 'call', {'key_in_data':dInput}).then(function (data) {
	    	    		  console.log(data);
	  				});
	    	        },
	    	        minLength: 3,
	    	        select: function( event, ui ) {
	    	          log( ui.item ?
	    	            "Selected: " + ui.item.label :
	    	            "Nothing selected, input was " + this.value);
	    	        },
	    	        open: function() {
	    	          $( this ).removeClass( "ui-corner-all" ).addClass( "ui-corner-top" );
	    	        },
	    	        close: function() {
	    	          $( this ).removeClass( "ui-corner-top" ).addClass( "ui-corner-all" );
	    	        }
	    	      });*/
	    	
	    });




	    
	    //$(oe_website_sale).find("input[name='search']").keyup();
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

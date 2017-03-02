
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
/*            if (index == items.length - 1) ul.append('<li id="0001" class="ui-menu-item" role="presentation"><a id="ui-id-0001" class="ui-corner-all" tabindex="-1">Search in all Brands</a></li>');
            if (index == items.length - 1) ul.append('<li id="0002" class="ui-menu-item" role="presentation"><a id="ui-id-0002" class="ui-corner-all" tabindex="-1">Search in all category</a></li>');
            if (index == items.length - 1) ul.append('<li id="0003" class="ui-menu-item" role="presentation"><a id="ui-id-0003" class="ui-corner-all" tabindex="-1">Search in all products</a></li>');
            */
//            if (index == items.length - 1){
//            	return $('<li>')
//            	.append('<a>' + item.category + '</a>')
//                .appendTo(ul);	
//            }
          });
        },
      });
    
    function getParameterByName(name, url) {
        if (!url) {
          url = window.location.href;
        }
        name = name.replace(/[\[\]]/g, "\\$&");
        var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
            results = regex.exec(url);
        if (!results) return null;
        if (!results[2]) return '';
        return decodeURIComponent(results[2].replace(/\+/g, " "));
    }   
    var search = getParameterByName('search');
    console.log(search);
    if(search != ""){
    	
    	$('#search').val(search)
    }
    
	$('.il_search').each(function () {
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
	    	 
/*	    	 	openerp.jsonRpc("/shop/get_products", 'call', {'key_in_data':dInput})
				.then(function (data) {
					availableTags = data
				});*/
	    	$(oe_website_sale).find("#search").catcomplete({
	            minLength: 0,
	            // substitute `source` for `url`
	            source: function(request, response) {
	            	var term = request.term;
	            	// get json 
	            	openerp.jsonRpc("/shop/get_products", 'call', {'key_in_data':dInput})
	            	.then(function success(data) {
	            		// filter results
	            		console.log(data);
	            			var res = $.grep(data, function(val) {
	            			return new RegExp($.ui.autocomplete.escapeRegex(term), "gi")
	            	})
	                , key = $.inArray(term.toUpperCase(), res)
	                , results = term.length === 1 
	                              & key !== -1 
	                              ? Array(res[key]) 
	                              : res;
	                response(results)
	              },function error(jqxhr, textStatus, errorThrown) {
	                   console.log(textStatus, errorThrown) // log `$.ajax` errors
	              	})
	          },select: function(event, ui) {
		    			
	  	            var selectedObj = ui.item;
	  	            console.log(selectedObj);
	  	            $('#search').val(dInput);
	  	            $('#categ_id').val(selectedObj.category);
	  	          
	  	            $search_value = selectedObj.label;
	  	            $partner_name = selectedObj.parent_name
	  	            

	  	            $remove_in = $search_value.replace(/^([^ ]+ ){2}/, '').toLowerCase();
	  	            $trim_string = $remove_in.trim();
	  	            $remove_special_char = $trim_string.replace(/[^a-z\d\s]+/gi, " ");
	  	            replace_space = $remove_special_char.replace(/\s+/g, '-');
	  	            
	  	            console.log(replace_space);
	  	            
	  	            if(selectedObj.parent_name){
	  	            	
	  	            	$remove_special_char = selectedObj.parent_name.replace(/[^a-z\d\s]+/gi, " ");
	  	            	parent_cat = $remove_special_char.replace(/\s+/g, '-').toLowerCase();
	  	            	console.log(parent_cat);
	  	            	$query_string = parent_cat+'-'+replace_space+'-'+selectedObj.category+'?search='+dInput;
	  	            }else{
	  	            	$query_string = replace_space+'-'+selectedObj.category+'?search='+dInput;
	  	            }
	  	           
	  	            
	  	            console.log(ui);
	  	            //$query_string = parent_cat+'-'+replace_space+'-'+selectedObj.category+'?search='+dInput;
	  	            
  	            
	  	            $("#ilsearch").attr("action", "/il/category/"+$query_string);
	  	            $("#ilsearch").submit();
	  	            return false;
	  	        },change: function () {
	  	          console.log($(this).val());
	  	        }
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

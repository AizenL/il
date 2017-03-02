$(document).ready(function () {
$('.oe_website_sale').each(function () {
    var $oe_website_sale = this;

    var delay = (function() {
        var timer = 0;
        return function(callback, ms) {
            clearTimeout(timer);
            timer = setTimeout(callback, ms);
        };
    })();  

   $($oe_website_sale).on("change", ".oe_cart1 input.js_quantity", function (ev) {
        ev.preventDefault();
        var $input = $(this);
        var value = parseInt($input.val(), 10);
        var line_id = parseInt($input.data('line-id'),10);
        console.log(line_id)
        var product_id = parseInt($input.data('product-id'),10);
        if (isNaN(value)) value = 0;
        delay(function() {
        	        
        openerp.jsonRpc("/shop/cart/update_json", 'call', {
            'line_id': line_id,
            'product_id': product_id,
            'set_qty': value})
            .then(function (data) {
            	console.log(data);
                if (!data.quantity) {
                    window.location.href = document.URL;
                    return false;
                }
                var $q = $(".my_cart_quantity");
                $q.parent().parent().removeClass("hidden", !data.quantity);
                $q.html(data.cart_quantity).hide().fadeIn(600);

                $input.val(data.quantity);
                $('input[name="'+product_id+'"]').val(data.quantity);
                $('.js_quantity[data-line-id='+line_id+']').val(data.quantity).html(data.quantity);
                $("#cart_total").replaceWith(data['website_sale.total']);
                return false;
            });
        }, 2000);
            return false;
            
    });

    $($oe_website_sale).on("change", ".products_item input.js_quantity_inherited", function () {
        var $input = $(this);
        var value = parseInt($input.val(), 10);
        if (isNaN(value)) value = 0;
        delay(function() {   

        openerp.jsonRpc("/shop/cart/update_json_shop_to_qty", 'call', {
        'product_id': parseInt($input.attr('name'),10),
        'set_qty': value})
        .then(function (data) {
        	console.log(data.quantity);
        if (!data.quantity) {
            location.reload();
            return;
        }
        var $q = $(".my_cart_quantity");
       
        $q.parent().parent().removeClass("hidden", !data.quantity);
        $q.html(data.cart_quantity).hide().fadeIn(600);

		var $p_id = parseInt($input.attr('name'),10);
        $('input[data-product-id="'+$p_id+'"]').val(data.quantity);
				$("#div_cart_total_new").replaceWith(data['website_sale.total']);
        $input.val(data.quantity);
        //$('.js_quantity[data-line-id='+line_id+']').val(data.quantity).html(data.quantity);
        $("#cart_total").replaceWith(data['website_sale.total']);
				//location.reload();
        return;
        });
        }, 2000);
    });




    $($oe_website_sale).on("change", "input.js_quantity_inherited2", function (ev) {
        ev.preventDefault();
        var $input = $(this);
        var value = parseInt($input.val(), 10);
        var product_id = $('#int_current_prod_variant_id').val(); 
        if (isNaN(value)) value = 0;
        //console.log("Function Calling /shop/product/");
        delay(function() {         
        openerp.jsonRpc("/shop/cart/update_json_shop_to_qty", 'call', {
        'product_id': product_id,//$('#int_current_prod_variant_id'),
        'set_qty': value})
        .then(function (data) {
        if (!data.quantity) {
            location.reload();
            //window.location.href = document.URL;
            return;
        }
        
        var $q = $(".my_cart_quantity");
        
        $q.parent().parent().removeClass("hidden", !data.quantity);
        $q.html(data.cart_quantity).hide().fadeIn(600);

		var $p_id = parseInt($input.attr('name'),10);
        $('input[data-product-id="'+$p_id+'"]').val(data.quantity);
				$("#div_cart_total_new").replaceWith(data['website_sale.total']);
        $input.val(data.quantity);
      
        $('.js_quantity[data-line-id='+line_id+']').val(data.quantity).html(data.quantity);
        $("#cart_total").replaceWith(data['website_sale.total']);
				//location.reload();
        return;
        });
        }, 2000);
    });
    //Senthil Code Start Here

    
    // Senthil Code End Here
 // inheriting original to set max to 99
 // hack to add and remove from cart with json
    var $my_qty_max = 9999;
    $($oe_website_sale).on('click', 'a.js_add_cart_json_inherited', function (ev) {
        ev.preventDefault();
        var $link = $(ev.currentTarget);
        var $input = $link.parent().parent().find("input");
        var min = parseFloat($input.data("min") || 0);
        var max = parseFloat($input.data("max") || $my_qty_max); //Infinity);
		var $p_id = parseInt($input.data('product-id'),10);
		
		//var min_order_qty = document.getElementById("minQty").getAttribute('data-minmum');
		//var order_type = document.getElementById("minQty").getAttribute('data-ordertype');
		var min_order_qty = parseFloat($input.data('minmum'));
		var order_type = $input.data('ordertype');		
		

		

		
		if (order_type == 'Multiple'){			
		var quantity = ($link.has(".fa-minus").length ? -parseFloat(min_order_qty) : parseFloat(min_order_qty)) + parseFloat($input.val(),10);
		}else{
        var quantity = ($link.has(".fa-minus").length ? -1 : 1) + parseFloat($input.val(),10);
		}
		
        $input.val(quantity > min ? (quantity < max ? quantity : max) : min);
				$('input[name="'+$p_id+'"]').val(quantity > min ? (quantity < max ? quantity : max) : min);
				$input.change();
        return false;
    });
    
/*    $($oe_website_sale).on('click', 'a.js_add_cart_json', function (ev) {
        ev.preventDefault();
        var $link = $(ev.currentTarget);
        var $input = $link.parent().parent().find("input");
        var input_value = parseInt($input.val(), 10);
        console.log(input_value);
      	var min = parseFloat($input.data("min") || 0);
        var max = parseFloat($input.data("max") || $my_qty_max); //Infinity);
		var $p_id = parseInt($input.data('product-id'),10);
		
		//var min_order_qty = document.getElementById("minQty").getAttribute('data-minmum');
		//var order_type = document.getElementById("minQty").getAttribute('data-ordertype');
		var min_order_qty = parseInt($input.data('minmum'),10);
		var order_type = $input.data('ordertype');		
		if (order_type == 'Multiple'){			
		var quantity = ($link.has(".fa-minus").length ? - parseFloat(min_order_qty) : parseFloat(min_order_qty)) + parseFloat($input.val(),10);
		var quantity = quantity - 1;
		}else{
        var quantity = ($link.has(".fa-minus").length ? -1 : 1) + parseFloat($input.val(),10);
        var quantity = quantity - 1;
		}
		
        console.log(input_value);
        
        $input.val(quantity > min ? (quantity < max ? quantity : max) : min);
				$('input[name="'+$p_id+'"]').val(quantity > min ? (quantity < max ? quantity : max) : min);
				$input.change();
        return false;
    });*/

	$($oe_website_sale).on("change", ".oe_cart input.js_quantity", function (ev) {
        ev.preventDefault();
        var $link = $(ev.currentTarget);
        var $input = $(this);
        var value = parseInt($input.val(), 10);
		var $product_id = parseInt($input.data('product-id'),10);
       	
		var line_id = parseInt($input.data('line-id'),10);
		
        if (isNaN(value)) value = 0;
        delay(function() {  
        openerp.jsonRpc("/shop/cart/update_json", 'call', {
            'line_id': line_id,
            'product_id': $product_id,
            'set_qty': value})
            .then(function (data) {
            	console.log(data);
                if (!data.quantity) {
                    window.location.href = document.URL;
                    return false;
                   
                }
                
                var $q = $(".my_cart_quantity");
                $q.parent().parent().removeClass("hidden", !data.quantity);
                $q.html(data.cart_quantity).hide().fadeIn(600);
                $input.val(data.quantity);
                
                $('.js_quantity[data-line-id='+line_id+']').val(data.quantity).html(data.quantity);
                $("#cart_total").replaceWith(data['website_sale.total']);
                return false;
            });
        }, 2000);
            return false;
    });

    $($oe_website_sale).on("click", ".oe_cart #clear_cart_button", function () {
        var $link = $(this);
        var line_id = parseInt($link.data('line-id'),10);
    	
    
        openerp.jsonRpc("/shop/cart/remove_order_line", 'call', {
            'line_id': line_id
            })
            .then(function (data) {
            	
                if (!data.line_id) {
                	window.location.href = document.URL;
                    return false;
                }
                return false;
            });
    });

 // inheriting original to set max to 99
 // hack to add and remove from cart with json
    var $my_qty_max = 9999;
    $($oe_website_sale).on('click', 'a.js_add_cart_json_inherited2', function (ev) {
        ev.preventDefault();
        var $link = $(ev.currentTarget);
        var $input = $link.parent().parent().find("input");
        var min = parseFloat($input.data("min") || 0);
        var max = parseFloat($input.data("max") || $my_qty_max); //Infinity);
        //var $p_id = parseInt($input.data('product-id'),10);
        var $p_id = document.getElementsByName("product_id")[0].value;
        
		//var min_order_qty = document.getElementById("minQty").getAttribute('data-minmum');
		//var order_type = document.getElementById("minQty").getAttribute('data-ordertype');
		var min_order_qty = parseFloat($input.data('minmum'));
		var order_type = $input.data('ordertype');
		//var min = parseFloat(min_order_qty)
		if (order_type == 'Multiple'){			
		var quantity = ($link.has(".fa-minus").length ? -parseFloat(min_order_qty) : parseFloat(min_order_qty)) + parseFloat($input.val(),10);
		}else{
			
		var quantity = ($link.has(".fa-minus").length ? -1 : 1) + parseFloat($input.val(),10);
		}
		
        
        //var quantity = ($link.has(".fa-minus").length ? -1 : 1) + parseFloat($input.val(),10);
        $input.val(quantity > min ? (quantity < max ? quantity : max) : min);
        $('input[name="'+$p_id+'"]').val(quantity > min ? (quantity < max ? quantity : max) : min);
        $input.change();
        return false;
    });

	$($oe_website_sale).on("change", ".oe_cart1 input.js_quantity", function (ev) {
        ev.preventDefault();
        var $input = $(this);
        var value = parseInt($input.val(), 10);
        var line_id = parseInt($input.data('line-id'),10);

        if (isNaN(value)) value = 0;
        openerp.jsonRpc("/shop/cart/update_json", 'call', {
            'line_id': line_id,
            'product_id': parseInt($input.data('product-id'),10),
            'set_qty': value})
            .then(function (data) {
            	console.log(data);
                if (!data.quantity) {
                	
                    window.location.href = document.URL;
                    return false;
                }

                $("#div_cart_total_new").replaceWith(data['website_sale.total']);
               
                var $q = $(".my_cart_quantity");
                $q.parent().parent().removeClass("hidden", !data.quantity);
                $q.html(data.cart_quantity).hide().fadeIn(600);
                $input.val(data.quantity);
                $('.js_quantity[data-line-id='+line_id+']').val(data.quantity).html(data.quantity);
                $("#cart_total").replaceWith(data['website_sale.total']);

                return false;
            });
    	});
        return false;

	});
});


function allow_numeric_input(e) {
 	// Allow: backspace, delete, tab, escape and enter (REMOVED: . == 190, decimalpoint == 110 )
	console.log(e);
	if ($.inArray(e.keyCode, [46, 8, 9, 27, 13]) !== -1 ||
	    // Allow: Ctrl+A, Command+A
	    (e.keyCode == 65 && ( e.ctrlKey === true || e.metaKey === true ) ) || 
	    // Allow: home, end, left, right, down, up
	    (e.keyCode >= 35 && e.keyCode <= 40)) {
		 // let it happen, don't do anything
		 return;
	}
        // Allow: 9+0=90, avoid: 0+9=09.
        var qty_inputed_value = document.getElementById("cart_quantity_txt_box").value;
        if (e.keyCode == 48 && qty_inputed_value < 1) {
            e.preventDefault();
        }
	if ((e.shiftKey || (e.keyCode < 48 || e.keyCode > 57)) && (e.keyCode < 96 || e.keyCode > 105)) {
	    e.preventDefault();
	}
}

/* -- with regex --
function allow_numeric_input(evt) {
  var theEvent = evt || window.event;
  var key = theEvent.keyCode || theEvent.which;
  key = String.fromCharCode( key );
  //var regex = /[0-9]|\./;
  var regex = /[0-9]/;
  if( !regex.test(key) ) {
    theEvent.returnValue = false;
    if(theEvent.preventDefault) theEvent.preventDefault();
  }
}
*/
/*
function on_load_call()
{
     var url = window.location.href;
     if(url.indexOf('/shop/product/') != -1){
        result = hide_all_add_to_cart_elements();
        var product_id = document.getElementsByName("product_id")[0].value;
        $("#int_current_prod_variant_id").val(product_id);

        result = get_cart_qty_for_selected_variant(product_id);
   }

}
on_load_call();*/



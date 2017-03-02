/* TO MOVE PRODUCT TO MY CART FROM BASKET */
function move_product_to_cart(ele) {
		//alert('move to cart');
    var tab_parent = ele.parentElement.parentElement.parentElement;
    var tr_parent = ele.parentElement.parentElement;
    var product_id = ele.parentElement.childNodes[1].value;
    //tab_parent.removeChild(tr_parent);
    //alert(product_id);
    console.log(product_id)
    
    $.ajax({ 
        url : "/shop/move_product_to_cart/product_id", 
        data: {product_id: product_id},
        success : function(data) {
        	 console.log(data)
					//var d = $.parseJSON(data);
					//alert('success');
        	//alert(data);
					//$("#hide_wshlist_poriduct").hide();
        	//location.reload();
        	window.location.href = document.URL;
        },
        error : function() {
					//location.reload();
					//alert(document.URL);
					//alert('error');
					//location.reload();
					window.location.href = document.URL;
        }
    });
     return false;
     
};



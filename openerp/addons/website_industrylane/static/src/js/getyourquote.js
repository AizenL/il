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

	$($oe_website_sale).on("click", ".requestQuote", function (ev) {
        ev.preventDefault();
        $product_id =  $(this).data("proid")
        var $dividis = '#dopprod-'+$product_id;
        var $showdiv = '#show-'+$product_id;
        console.log($product_id);

        if ($product_id);
        openerp.jsonRpc("/shop/update_get_your_quote", 'call', {
            'product_id': parseInt($product_id,10)})
            .then(function (data) {
            	if(data== 'Duplicate'){
            		alert("Product is already added!");
            	}
            	console.log(data.result);
            	// $('#MessageBox').modal('toggle');
            	console.log($dividis);
            	$("#button_requestQuote").load(location.href + " #button_requestQuote");
            	//$($dividis).addClass("hidden");
            	//$($showdiv).toggle();
                   // window.location.href = document.URL;
                return false;
               
            });
        
    	});
        return false;

	});
});





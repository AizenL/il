$(function(){
	"use strict";
     
	/*-------------- Pre-loader ------------------*/	
	$("#loading").delay(500).fadeOut(2000);
		$("#loading-center").on('click',function() {
			$("#loading").fadeOut(1000);
		});	
	/**
	 * gallery
	 */
	$('.gallery').each(function(){
		
		$(this).magnificPopup({
			delegate: 'a', // child items selector, by clicking on it popup will open
		  	type: 'image',
			gallery:{
			    enabled:true
			}
		});
		
	})
	

$( document ).ready(function() {
    var heights = $(".well").map(function() {
        return $(this).height();
    }).get(),

    maxHeight = Math.max.apply(null, heights);
    $(".well").height(maxHeight);
});	
	
  $(document).ready(function(){
        $('.dropdown-toggle').dropdown()
    });
 
	var mapMarkers = [
		{
			"id": "1",
			"title": "Industrylane",
			"address": "No.58, 3rd floor, Railway Parallel Road, Kumara Park West, Bengaluru - 560020",
			"custompinimage": "images\/pin.png"
		}
	]  
    
$('#clear_all').click(function(){
	
	var pageURL = $(location).attr("href");	
    
    var NewpageURL = pageURL.split( '&' )[0];
    console.log(NewpageURL);
    window.location.replace(NewpageURL);
});	
	        // accordion widget

	
    var demo1 = $('select[name="multipleSelect"]').bootstrapDualListbox();
    $("#spcial").submit(function() {
     var pro = $('select[name="multipleSelect"]').val();
     console.log(pro);
     $('#chag_sort').val(pro);
    });
    
    var selectedValues = $('#multipleSelect').val();
    console.log(selectedValues);
  
     $('#login-overlay').magnificPopup({
          type: 'inline',
          preloader: false,
          focus: '#name',

          // When elemened is focused, some mobile browsers in some cases zoom in
          // It looks not nice, so we disable it:
          callbacks: {
            beforeOpen: function() {
              if($(window).width() < 700) {
                this.st.focus = false;
              } else {
                this.st.focus = '#name';
              }
            }
          }
        });	
	
	$(document).ready(function() {
'use strict';
	var owl = $("#owl-clients");
	  owl.owlCarousel({
	      items : 7, //10 items above 1000px browser width
	      itemsDesktop : [1000,5], //5 items between 1000px and 901px
	      itemsDesktopSmall : [900,3], // betweem 900px and 601px
	      itemsTablet: [600,2], //2 items between 600 and 0
	      itemsMobile : true, // itemsMobile disabled - inherit from itemsTablet option
		navigation: true,
   	    pagination : false,
   	 rewindNav:false,
   	    loop:true,
	    navigationText: ["<i class='fa fa-angle-left'></i>","<i class='fa fa-angle-right'></i>"],
	});
});
	
	$(document).ready(function(){
		$('.requestQuote').on('click',function(){
			//Scroll to top if cart icon is hidden on top
			$('html, body').animate({
				'scrollTop' : $("#button_requestQuote").position().top
			});
			//Select item image and pass to the function
			var itemImg = $(this).parent().find('.images-container img').eq(0);
			//var src = $(this).closest(".images-container").find(".img-responsive").attr("src");
			//alert(src);
			flyToElement($(itemImg), $('#button_requestQuote'));
		});
	});	
	
	// dropdown in leftmenu
	jQuery('.leftmenu .dropdown > a').click(function(){
		if(!jQuery(this).next().is(':visible'))
			jQuery(this).next().slideDown('fast');
		else
			jQuery(this).next().slideUp('fast');	
		return false;
	});
	
	if(jQuery.uniform) 
	   jQuery('input:checkbox, input:radio, .uniform-file').uniform();
		
	if(jQuery('.widgettitle .close').length > 0) {
		  jQuery('.widgettitle .close').click(function(){
					 jQuery(this).parents('.widgetbox').fadeOut(function(){
								jQuery(this).remove();
					 });
		  });
	}
	
	
	
	/*-------------- Responsive-Menu ------------------*/	
	jQuery(function ($) {
		var menu = $('.rm-nav').rMenu({
		});
	});
		
	/**
	 * Maps
	 */
	$( '.js-where-we-are' ).each( function () {
		new SimpleMap( $( this ), {
			markers: mapMarkers,
			zoom:    $( this ).data( 'zoom' ),
			type:    $( this ).data( 'type' ),
			styles:  [{"featureType":"administrative","elementType":"labels.text.fill","stylers":[{"color":"#444444"}]},{"featureType":"landscape","elementType":"all","stylers":[{"color":"#f2f2f2"}]},{"featureType":"landscape.man_made","elementType":"geometry.fill","stylers":[{"color":"#eeeeee"}]},{"featureType":"landscape.natural.landcover","elementType":"geometry.fill","stylers":[{"color":"#dddddd"}]},{"featureType":"landscape.natural.terrain","elementType":"geometry.fill","stylers":[{"color":"#dddddd"}]},{"featureType":"poi","elementType":"all","stylers":[{"visibility":"off"}]},{"featureType":"road","elementType":"all","stylers":[{"saturation":-100},{"lightness":45}]},{"featureType":"road.highway","elementType":"all","stylers":[{"visibility":"simplified"}]},{"featureType":"road.arterial","elementType":"labels.icon","stylers":[{"visibility":"off"}]},{"featureType":"transit","elementType":"all","stylers":[{"visibility":"off"}]},{"featureType":"water","elementType":"all","stylers":[{"color":"#007cc3"},{"visibility":"on"}]},{"featureType":"water","elementType":"geometry.fill","stylers":[{"color":"#1f425d"}]},{"featureType":"water","elementType":"labels.text.fill","stylers":[{"color":"#979797"}]},{"featureType":"water","elementType":"labels.text.stroke","stylers":[{"weight":"0.01"}]}],
		}).renderMap();
	});
	
	$( '.route' ).each( function () {
		new SimpleMap( $( this ), {
			zoom:    $( this ).data( 'zoom' ),
			type:    $( this ).data( 'type' ),
			styles:  [{"featureType":"administrative","elementType":"labels.text.fill","stylers":[{"color":"#444444"}]},{"featureType":"landscape","elementType":"all","stylers":[{"color":"#f2f2f2"}]},{"featureType":"landscape.man_made","elementType":"geometry.fill","stylers":[{"color":"#eeeeee"}]},{"featureType":"landscape.natural.landcover","elementType":"geometry.fill","stylers":[{"color":"#dddddd"}]},{"featureType":"landscape.natural.terrain","elementType":"geometry.fill","stylers":[{"color":"#dddddd"}]},{"featureType":"poi","elementType":"all","stylers":[{"visibility":"off"}]},{"featureType":"road","elementType":"all","stylers":[{"saturation":-100},{"lightness":45}]},{"featureType":"road.highway","elementType":"all","stylers":[{"visibility":"simplified"}]},{"featureType":"road.arterial","elementType":"labels.icon","stylers":[{"visibility":"off"}]},{"featureType":"transit","elementType":"all","stylers":[{"visibility":"off"}]},{"featureType":"water","elementType":"all","stylers":[{"color":"#007cc3"},{"visibility":"on"}]},{"featureType":"water","elementType":"geometry.fill","stylers":[{"color":"#1f425d"}]},{"featureType":"water","elementType":"labels.text.fill","stylers":[{"color":"#979797"}]},{"featureType":"water","elementType":"labels.text.stroke","stylers":[{"weight":"0.01"}]}],
		}).renderMap();
	});
	
	
	/**
	 * Number Counter Widget JS code
	 */
	// Get all number counter widgets
	var $counterWidgets = $( '.widget-number-counters' );

	if ( $counterWidgets.length ) {
		$counterWidgets.each( function () {
			new NumberCounter( $( this ) );
		} );
	}
	$.clearInput = function () {
        $('#customerform').find('input[type=text], input[type=tel], input[type=number], input[type=email], textarea').val('');
        //$('#supplier_register').find('input[type=text], input[type=tel], input[type=number], input[type=email], textarea').val('');
	};	
	
	
/*	$("#supplier_register").submit(function(e) {

	    var url = "/supplier_ac"; // the script where you handle the form input.

	    $.ajax({
	           type: "POST",
	           url: url,
	           data: $("#supplier_register").serialize(), // serializes the form's elements.
	           success: function(data)
	           {
	        	   jQuery("#simple-msg").html('<div class="alert alert-success fade in alert-dismissable">'+data+'</div>');
	        	   $.clearInput();
	           },
	           error: function(jqXHR, textStatus, errorThrown){
	        	   jQuery("#simple-msg").html('<div class="alert alert-warning fade in alert-dismissable">'+data+'</div>');
	        	   $.clearInput();
	           }
	         });

	    e.preventDefault(); // avoid to execute the actual submit of the form.
	});*/
	

	$("#customerform").submit(function(e) {

	    var url = "/home_customer_form"; // the script where you handle the form input.

	    $.ajax({
	           type: "POST",
	           url: url,
	           data: $("#customerform").serialize(), // serializes the form's elements.
	           success: function(data)
	           {
	        	   jQuery("#simple-msg").html('<div class="alert alert-success fade in alert-dismissable">'+data+'</div>');
	        	   $.clearInput();
	        	   $('#modal-customerform').delay(1500).fadeOut('slow');
	        	   setTimeout(function(){
	        		   $('#modal-customerform').modal("hide");
	        	   }, 2000);
	        	  
	        	   
	           },
	           error: function(jqXHR, textStatus, errorThrown){
	        	   jQuery("#simple-msg").html('<div class="alert alert-warning fade in alert-dismissable">'+data+'</div>');
	        	   $.clearInput();
	           }
	         });

	    e.preventDefault(); // avoid to execute the actual submit of the form.
	});
/*	   $('#customerform').on('hidden.bs.modal', function() {
		   this.modal('show');
		 });*/	   

	$('#customerform').submit(function() {
		setTimeout(function(){
			  $('#customerform').modal('hide')
			}, 4000);
	});	

	/* Mega Menu */
	$('.mega-menu-title').on('click',function(){
		if($('.mega-menu-category').is(':visible')){
			$('.mega-menu-category').slideUp();
		} else {
			$('.mega-menu-category').slideDown();
		}
	});
    
    
    $('.mega-menu-category .nav > li').hover(function(){
    	$(this).addClass("active");
		$(this).find('.popup').stop(true,true).fadeIn('slow');
    },function(){
        $(this).removeClass("active");
		$(this).find('.popup').stop(true,true).fadeOut('slow');
    });
    
    
	$('.mega-menu-category .nav > li.view-more').on('click',function(e){
		if($('.mega-menu-category .nav > li.more-menu').is(':visible')){
			$('.mega-menu-category .nav > li.more-menu').stop().slideUp();
			$(this).find('a').text('More category');
		} else { 
			$('.mega-menu-category .nav > li.more-menu').stop().slideDown();
			$(this).find('a').text('Close menu');
		}
		e.preventDefault();
	});	

	
	$(".BillingInfo").validate({
		rules: {
			name: "required",
			shipping_name: "required",
			shipping_street: "required",			
			phone: {
				required:true, 
				digits: true,				
		        minlength:11,
		        maxlength:11
		    },
		    shipping_phone: {
				required:true,
				digits: true,				
		        minlength:11,
		        maxlength:11
		    },		    
		    email: {
				required: true,
				email: true
			},
			mobile: {
				digits: true,
				minlength:10,
				maxlength:10
		    },
		    shipping_mobile: {
				digits: true,
				minlength:10,
				maxlength:10
		    },			    
		    zip: {
				required:true,  
				digits: true,
				minlength:6,   
		    },				
		    shipping_zip: {
				required:true,  
				digits: true,
				minlength:6,   
		    },				
		},
		messages: {
			name: "Please enter your Name",
			shipping_name: "Please enter your Name",				
			phone: {
				required: "Phone number is Required",
				minlength: "It is not valid Phone number. e.g: 08099632658"
			},
			shipping_phone: {
				required: "Phone number is Required",
				minlength: "It is not valid Phone number. e.g: 08099632658"
			},	
			mobile: {
				minlength: "It is not valid Mobile Number"
			},	
			shipping_mobile: {
				minlength: "It is not valid Mobile Number"
			},				
			zip: {
				required: "Postal code is required",
				minlength: "It is not valid Postal Code"
			},		
			shipping_zip: {
				required: "Postal code is required",
				minlength: "It is not valid Postal Code"
			},				
			email: "Please enter a valid email address",

		}
	});
	

	
	$("#spcial").validate({
		rules: {
			partner_name: "required",
			contact_name: "required",
			email_from: {
				required:true,
				email: true
			},
			phone: {
				required:true, 
				digits: true,				
		        minlength:11,
		        maxlength:11
		    },
		    name: "required",	
		    name: "required",			
		},
		messages: {
			partner_name: "Please enter name of the company",
			contact_name: "Please enter Contact Name",				
			phone: {
				required: "Phone number is Required",
				minlength: "It is not valid Phone number. e.g: 08099632658"
			},
			email_from: {
				required: "Email is Required",
				email: "Please enter a valid email address"
			},	
			name: "Subject Field is Required",

		}
	});
		
	
	$("#customerform").validate({
		rules: {
			contact_name: "required",
			partner_name: "required",			
			mobile: {
				required:true,  
		        minlength:10,
		        maxlength:10
		    },   
		    email_from: {
				required: true,
				email: true
			},
			
		},
		messages: {
			contact_name: "Please enter Contact Name",
			partner_name: "Please enter your Company Name",
			mobile: {
				required: "Mobile number is required",
				minlength: "It is not valid Mobile number"
			},
		
			email_from: "Please enter a valid email address",

		}
	});	
	
	$("#supplier_register").validate({
		rules: {
			name: "required",
			concern_person: "required",			
			mobile: {
				required:true,  
		        minlength:10,
		        maxlength:10
		    },
		    zip: {
				required:true,  
				digits: true,
		        maxlength:6
		    },		    
		    email: {
				required: true,
				email: true
			},
		},
		messages: {
			name: "Please enter your Name",
			mobile: {
				required: "Mobile number is Required",
				minlength: "It is not valid Mobile number"
			},
			email: "Please enter a valid email address",

		}
	});	
	
	
    $("#special-offer .owl").owlCarousel({
        autoPlay : false,
        items : 1,
        itemsDesktop : [1199,1],
        itemsDesktopSmall : [991,1],
        itemsTablet: [767,2],
        itemsMobile : [480,1],
        slideSpeed : 3000,
        paginationSpeed : 3000,
        rewindSpeed : 3000,
        navigation : true,
        stopOnHover : true,
        pagination : false,
        scrollPerPage:true,
        navigation:true,
        navigationText: [
           "<i class='fa fa-chevron-left'></i>",
           "<i class='fa fa-chevron-right'></i>"
        ]        
    });	
	/**
	 * Quick quote form submission
	 */
	
	// Contact Form Request
	$(".validate").validate();
	$(document).on('submit', '#SignUpForm', function() {
		//console.log("Test");
		$.ajax({
			url : 'contact/send_mail.php',
			type : 'post',
			dataType : 'json',
			data : $(this).serialize(),
			success : function(data) {
				if (data == true) {
					$('.form-respond').html("<div class='content-message alert alert-success'><a href='#' class='close' data-dismiss='alert' aria-label='close'>&times;</a><p>Your message has been submitted.</p> </div>");
				} else {
					$('.form-respond').html("<div class='content-message alert alert-danger'><a href='#' class='close' data-dismiss='alert' aria-label='close'>&times;</a><p>Error sending. Try again later.</p> </div>");
				}
			},
			error : function(xhr, err) {
				$('.form-respond').html("<div class='content-message alert alert-danger'><a href='#' class='close' data-dismiss='alert' aria-label='close'>&times;</a><p>Try again later.</p> </div>");
			}
		});
		return false;
	});
	
	$(document).on('submit', '#CustomerSignUp', function() {
		console.log("Test");
		$.ajax({
			url : 'http://52.212.165.143/contact/customer.php',
			type : 'post',
			dataType : 'json',
			data : $(this).serialize(),
			success : function(data) {
				if (data == true) {
					$('.form-respond').html("<div class='content-message alert alert-success'><a href='#' class='close' data-dismiss='alert' aria-label='close'>&times;</a><p>Your message has been submitted.</p> </div>");
				} else {
					$('.form-respond').html("<div class='content-message alert alert-danger'><a href='#' class='close' data-dismiss='alert' aria-label='close'>&times;</a><p>Error sending. Try again later.</p> </div>");
				}
			},
			
			error : function(xhr, err) {
				console.log(error);
				$('.form-respond').html("<div class='content-message alert alert-danger'><a href='#' class='close' data-dismiss='alert' aria-label='close'>&times;</a><p>Try again later.</p> </div>");
			}
		});
		return false;
	});	
	
	
	

	/* Mega Menu */
	$('.mega-menu-title').on('click',function(){
		if($('.mega-menu-category').is(':visible')){
			$('.mega-menu-category').slideUp();
		} else {
			$('.mega-menu-category').slideDown();
		}
	});
    
    
    $('.mega-menu-category .nav > li').hover(function(){
    	$(this).addClass("active");
		$(this).find('.popup').stop(true,true).fadeIn('slow');
    },function(){
        $(this).removeClass("active");
		$(this).find('.popup').stop(true,true).fadeOut('slow');
    });
    
    
	$('.mega-menu-category .nav > li.view-more').on('click',function(e){
		if($('.mega-menu-category .nav > li.more-menu').is(':visible')){
			$('.mega-menu-category .nav > li.more-menu').stop().slideUp();
			$(this).find('a').text('More category');
		} else { 
			$('.mega-menu-category .nav > li.more-menu').stop().slideDown();
			$(this).find('a').text('Close menu');
		}
		e.preventDefault();
	});	
	
$('ul.nav li.dropdown').hover(function() {
  $(this).find('.dropdown-menu').stop(true, true).delay(200).fadeIn(500);
}, function() {
  $(this).find('.dropdown-menu').stop(true, true).delay(200).fadeOut(500);
});	
	
	/**
	 * Request quote scroll
	 */
    $('#button_requestQuote').on('click', function(){
        
        $('html, body').animate({
	        scrollTop: $("#quickQuoteForm_wrapper").offset().top
	    }, 2000);
            
    });

    $('a#overview').on('click', function(){
        
        $('html, body').animate({
	        scrollTop: $("#overviewpanel").offset().top
	    }, 2000);
            
    });		
	
    $('a#Value').on('click', function(){
        
        $('html, body').animate({
	        scrollTop: $("#ValueProposition").offset().top
	    }, 2000);
            
    });		
	/*
    $('a.products').on('click', function(){
        
        $('html, body').animate({
	        scrollTop: $("#portfolio").offset().top
	    }, 2000);
            
    });	
	    $('a#features').on('click', function(){
        
        $('html, body').animate({
	        scrollTop: $("#Ourfeatures").offset().top
	    }, 2000);
            
    });	
	*/
    $('a#teamil').on('click', function(){
        
        $('html, body').animate({
	        scrollTop: $("#TeamIndustrylane").offset().top
	    }, 2000);
            
    });	
	
	    $('a#Testimonials').on('click', function(){
        
        $('html, body').animate({
	        scrollTop: $("#testimonials_panel").offset().top
	    }, 2000);
            
    });	
	
    $('a#supplier').on('click', function(){
        
        $('html, body').animate({
	        scrollTop: $("#HowTo").offset().top
	    }, 2000);
            
    });		
	
    $('a#job').on('click', function(){
        
        $('html, body').animate({
	        scrollTop: $("#Careers").offset().top
	    }, 2000);
            
    });			
	
//Back To Top
	$(window).scroll(function() {
		if ($(window).scrollTop() > 400) {
			$("#back-top").fadeIn(200);
		} else {
			$("#back-top").fadeOut(200);
		}
	});
	$('#back-top').click(function() {
		$('html, body').stop().animate({
			scrollTop : 0
		}, 500, 'easeInOutExpo');
	});
		
$('.carousel').carousel({
  interval: 5000
})		
	
		var $portfolio_selectors = $('.portfolio-filter a');
		
		if($portfolio_selectors.length) {
			
			var $portfolio = $('.portfolio-items');
			$portfolio.isotope({
				itemSelector : '.portfolio-item',
				filter: '.all', 
				layoutMode : 'fitRows'
			});
			
			$portfolio_selectors.on('click', function(){
				$portfolio_selectors.removeClass('active');
				$(this).addClass('active');
				var selector = $(this).attr('data-filter');
				$portfolio.isotope({ filter: selector });
				return false;
			});
		}
	
})



$(document).ready( function() {

	$('.hwsyl.gallery-item').hover( function() {
		$(this).find('.hwsyl.img-title').fadeIn(300);
	}, function() {
		$(this).find('.hwsyl.img-title').fadeOut(100);
	});
	
});


$(document).ready( function() {
	//$( ".top__menu #top_menu li" ).last().css( "display", "none" );
	//$( ".top__menu #top_menu .dropdown-menu li" ).last().css( "display", "block" );
	$("#top_menu b").replaceWith(function() { return this.innerHTML; });	
	$('.gallery-item').hover( function() {
		$(this).find('.img-title').fadeIn(300);
	}, function() {
		$(this).find('.img-title').fadeOut(100);
	});
	
	
	$("#customer_form").validator().on("submit", function (event) {
	    if (event.isDefaultPrevented()) {
	        // handle the invalid form...
	    	console.log("Error In Form");
	        formError();
	        submitMSG(false, "Did you fill in the form properly?");
	    } else {
	        // everything looks good!
	    	console.log("No Error");
	        event.preventDefault();
	        submitForm();
	    }
	});
	

	function formSuccess(){
	    $("#customer_form")[0].reset();
	    submitMSG(true, "Message Submitted!")
	}

	function formError(){
	    $("#customer_form").removeClass().addClass('shake animated').one('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function(){
	        $(this).removeClass();
	    });
	}	
	
	function submitMSG(valid, msg){
	    if(valid){
	        var msgClasses = "h3 text-center tada animated text-success";
	    } else {
	        var msgClasses = "h3 text-center text-danger";
	    }
	    $("#msgSubmit").removeClass().addClass(msgClasses).text(msg);
	}
	
	
	function submitForm(){
	    // Initiate Variables With Form Content
	    var name = $("#name").val();
	    var partner_name = $("#partner_name").val();
	    var phone = $("#phone").val();
	    var email_from = $("#email_from").val();	
		
	var person = {
				"name": name,
				"partner_name": partner_name,
				"phone": phone,
				"email_from": email_from,
	};		
		
		$.ajaxPrefilter( function( options ) {
		  if ( options.crossDomain ) {
			var newData = {};
			// Copy the options.data object to the newData.data property.
			// We need to do this because javascript doesn't deep-copy variables by default.
			newData.data = $.extend({}, options.data);
			newData.url = options.url;
			console.log();
			// Reset the options object - we'll re-populate in the following lines.
			options = {person};
		
			// Set the proxy URL
			options.url = "http://localhost:8069";
			options.data = $.param(person);
			options.crossDomain = false;
		  }
		});	
		
			$.ajax({
			  url: '/home_customer_form/',
			type : 'POST',
			  data: JSON.stringify(person),
			  crossDomain: true, // set this to ensure our $.ajaxPrefilter hook fires
			  processData: false // We want this to remain an object for  $.ajaxPrefilter
			}).success(function(data) { // Use the jQuery promises interface
				var jsonData = jQuery.parseJSON(JSON.stringify(data)); // Assume it returns a JSON string
				console.log(jsonData); // Do whatever you want with the data
				//$('#msgSubmit').html("<div class='content-message'> <i class='fa fa-rocket fa-4x'></i> <h2> Form Submitted Successfully</h2> </div>");
				$('#MyRegistration').modal( 'hide' );
				 $('#MessageBox').modal('toggle');
			});	
	}
	
	
});



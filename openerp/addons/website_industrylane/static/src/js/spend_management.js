	function spend_management (data) {
    // Create the chart
		var defaultTitle = "Consolidated Month-Wise Spend Report";
		var drilldownTitle = "Spend Report :  ";
		var defaultSeriesTitle = "Amount";
		Highcharts.setOptions({
			lang: {
				 drillUpText: '◁ Back',
				 viewData: ''
			}
		});			
    $('#container').highcharts({
        chart: {
        	type: 'pie', 
            options3d: {
                enabled: true,
                alpha: 45,
                beta: 0
            },        	
           events: {
                drilldown: function (e) {
                	var chart = this
                	chart.setTitle({ text: drilldownTitle + e.point.name });
                	if (!e.seriesOptions) {
                        chart.setTitle({ text: drilldownTitle + e.point.name });
                        var drilldowns=[];                        
                	    openerp.jsonRpc("/shop/get_smdrilldown_data", 'call', {
                	     'name': e.point.name
	               	    })
	               		.then(function (data) {
	               			chart.hideLoading();
	                        chart.addSeriesAsDrilldown(e.point, data);
	                       
	               		});

                    }

                },
                drillup: function(e) {
                	var chart = this
                    chart.setTitle({ text: defaultTitle });
                }
            }
      
        },
        title: {
            text: defaultTitle
        },

        legend: {
            enabled: false
        },

        plotOptions: {
        	 pie: {
                 allowPointSelect: true,
                 cursor: 'pointer',
                 depth: 35,
                 dataLabels: {
                     enabled: true,
                     format: '{point.name}'
                 }
             },
        	series: {
                borderWidth: 0,
                dataLabels: {
                    enabled: true,
                    format: '{point.name}'
                }
            }
        },

        series: [{
            colorByPoint: true,
            name:defaultSeriesTitle,
            data: data
        }],

        drilldown: {
        	  series: []
        }
    });
	}    
	
	
	function trand_analysis (data) {
		var defaultTitle = "Consolidated Month-Wise Trend Analysis Report";
		var defaultSeriesTitle = "Amount";
		var drilldownTitle = "Trend Analysis :  ";	
		Highcharts.setOptions({
			lang: {
				 drillUpText: '◁ Back'
			}
		});		
		 $('#trand_analysis').highcharts({
		        chart: {
		            type: 'column',	            
		            events: {
		                drilldown: function (e) {
		                	var chart = this
		                	chart.setTitle({ text: drilldownTitle + e.point.name });
		                	if (!e.seriesOptions) {
		                       console.log(e);
		                       
		                        chart.setTitle({ text: drilldownTitle + e.point.name });
		                        chart.xAxis[0].setTitle({ text: "Month" });
		                        
		                        var drilldowns=[];                        
		                	    openerp.jsonRpc("/shop/trand_analysis_line", 'call', {
		                	     'name': e.point.name
			               	    })
			               		.then(function (data) {
			               			chart.hideLoading();
			                        chart.addSeriesAsDrilldown(e.point, data);

			               		});

		                    }

		                },
		                drillup: function(e) {
		                	var chart = this
		                    chart.setTitle({ text: defaultSeriesTitle });
		                	//chart.setTitle({ text: 'Month' });
		                	chart.xAxis[0].setTitle({ text: "Category" });
		                }
		            }
		        },
		        title: {
		            text: defaultTitle
		        },
		        xAxis: {
		            type: 'category'
		            	
		        },
		        plotOptions: {
		            column : {
		                stacking : 'normal'
		            },
	        
		        },

		        series: [{
		            colorByPoint: true,
		            name:defaultSeriesTitle,
		            data: data
		        }],
		        drilldown: {
		        	 series: []
		            /*series: [{
		                name: 'Widget A',
		                type: 'line',
		                id: 'CUTTING TOOL',
		                data: [
		                    {name: 'Qtr 1', y: 5},
		                    {name: 'Qtr 2', y: 25},
		                    {name: 'Qtr 3', y: 25},
		                    {name: 'Qtr 4', y: 20}
		                ]
		            }
		           ]*/
		        }
		    })
		}  	

$(document).ready(function () {
	
	$('#spend_management').each(function () {
	    openerp.jsonRpc("/shop/get_sm_data", 'call', {
	    	 type : "GET",
	    })
		.then(function (data) {
			spend_management(data);
			 console.log(data);
		});
	    
	    openerp.jsonRpc("/shop/trand_analysis", 'call', {
	    	 type : "GET",
	    })
		.then(function (data) {
			trand_analysis(data);
			 console.log(data);
		});
	});
});


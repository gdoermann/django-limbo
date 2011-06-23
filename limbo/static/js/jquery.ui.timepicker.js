/*
 * A time picker for jQuery UI
 * Based on the timePicker by Anders Fajerson (http://perifer.se) -
 * Copyright (c) 2009 Anders Fajerson
 *
 * Dual licensed under the MIT and GPL licenses.
 * Copyright (c) 2010 Gregory Doermann
 * @name     timepicker
 * @version  0.1
 * @author   Greg Doermann (http://www.snirk.com)
 * @example  $("#mytime").timepicker();
 * @example  $("#mytime").timepicker({step:30, startTime:"15:00", endTime:"18:00"});
 */
(function($) {
	$.widget("ui.timepicker", {
		options: {
			step:15,
			startTime: new Date(0, 0, 0, 0, 0, 0),
			endTime: new Date(0, 0, 0, 23, 45, 0),
			separator: ':',
			show24Hours: false,
			source:null,
			am:'am',
			pm:'pm'
		},
		_create: function(){
			var self = this;
			var elm = this.element;
			this.elm = elm;
			var input = $(elm);
			var startTime = this._timeToDate(this.options.startTime);
			var endTime = this._timeToDate(this.options.endTime);
			var initial = elm.val();
			this.initial = initial;
			
			if (this.options.source == null){
				var times = [];
				var time = new Date(startTime); // Create a new date object.
				while(time <= endTime) {
					times[times.length] = self._formatTime(time);
					time = new Date(time.setMinutes(time.getMinutes() + this.options.step));
				}
				this.options.source = times;
			}
			var options = this.options;
			this._set_source(options.source);
			
			$("<button>&nbsp;</button>")
				.css('min-height', '2em')
				.attr("tabIndex", -1)
				.attr("title", "Show All Times")
				.insertAfter(input)
				.button({
					icons: {
						primary: "ui-icon-triangle-1-s"
					},
					text: false
				}).removeClass("ui-corner-all")
				.addClass("ui-corner-right ui-button-icon")
				.click(function() {
					// close if already visible
					if (input.autocomplete("widget").is(":visible")) {
						input.autocomplete("close");
						return false;
					}
					// pass empty string as value to search for, displaying all results
					input.autocomplete("search", "");
					input.autocomplete("widget").css('z-index', '1010 !important')
					input.focus();
					return false;
				});
		},
		_set_source: function(source){
			var options = this.options;
			this.elm.autocomplete({
				source: options.source,
				delay: 0,
				minLength: 0
				})
				.addClass("ui-widget ui-widget-content ui-corner-left");
			
		},
		_formatTime: function (time, settings) {
			var h = time.getHours();
			var hours = this.options.show24Hours ? h : (((h + 11) % 12) + 1);
			var minutes = time.getMinutes();
			return this._formatNumber(hours) + this.options.separator + this._formatNumber(minutes) + (this.options.show24Hours ? '' : ((h < 12) ? ' ' + this.options.am : ' ' + this.options.pm));
		},
		_formatNumber: function (value) {
			return (value < 10 ? '0' : '') + value;
		},
		_timeToDate: function (input) {
			return (typeof input == 'object') ? this._normaliseTime(input) : this._timeStringToDate(input);
		},
		_timeStringToDate: function (input) {
			if (input) {
				var array = input.split(self.options.separator);
				var hours = parseFloat(array[0]);
				var minutes = parseFloat(array[1]);
	
				// Convert AM/PM hour to 24-hour format.
				if (!self.options.show24Hours) {
				if (hours === 12 && input.substr(this.options.am) !== -1) {
					hours = 0;
				}
				else if (hours !== 12 && input.indexOf(this.options.pm) !== -1) {
					hours += 12;
				}
				}
				var time = new Date(0, 0, 0, hours, minutes, 0);
				return this._normaliseTime(time);
			}
			return null;
		},
		/* Normalise time object to a common date. */
		_normaliseTime: function (time) {
			time.setFullYear(2001);
			time.setMonth(0);
			time.setDate(0);
			return time;
		}
	});

})(jQuery);

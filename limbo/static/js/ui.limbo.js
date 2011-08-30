var LIMBO = window.LIMBO;

function create_uuid() {
    var uuid = (function () {
        var i,
            c = "89ab",
            u = [];
        for (i = 0; i < 36; i += 1) {
            u[i] = (Math.random() * 16 | 0).toString(16);
        }
        u[8] = u[13] = u[18] = u[23] = "-";
        u[14] = "4";
        u[19] = c.charAt(Math.random() * 4 | 0);
        return u.join("");
    })();
    return {
        toString: function () {
            return uuid;
        },
        valueOf: function () {
            return uuid;
        }
    };
}

(function($) {
    // TODO: Use the title attr to link the picker, start and end components together or, even better, a fieldset
    $.widget("ui.range_picker", {
        options: {
            onChange:null
        },
        _create: function() {
            var obj = this.element;
            var $$ = this.obj = this.$$ = $(obj);
            var parent = this;

            function refresh_pickers(){
                // TODO: Fix this so they are dependant on one another...
//                try{
//                    parent.start_end.datepicker('destroy');
//                } catch (e){}
//                parent.datepickers = parent.start_end.datepicker({
//                    defaultDate: "+1d",
//                    changeMonth: true,
//                    numberOfMonths: 1,
//                    onClose:function(){
//                        if ($(this).val() != ''){
//                            parent.picker.find('.ui-state-active').removeClass('ui-state-active');
//                            parent.picker.find('input[checked=checked').attr('checked', '');
//                        }
//                    },
//                    onSelect: function(selectedDate){
//                        var option;
//                        if (this.id == "id_start_date" || this.id == "id_qa_table-start_date"){
//                            option = "minDate";
//                        }else{
//                            option = "maxDate";
//                        }
//                        //var option = this.id == "id_start_date" ? "minDate" : "maxDate",
//                        instance = $( this ).data( "datepicker" ),
//                        date = $.datepicker.parseDate(
//                            instance.settings.dateFormat ||
//                            $.datepicker._defaults.dateFormat,
//                            selectedDate, instance.settings
//                        );
//                        parent.datepickers.not( this ).datepicker( "option", option, date );
//                    }
//                });
            }

            function refresh(){
                parent.picker = obj;
                parent.start = obj.parent().siblings().children('.start_date');
                parent.end = obj.parent().siblings().children('.end_date');
                parent.start_end = obj.parent().siblings().children('.start_date, .end_date');
                parent.picker.find('input').click(function(){
                    parent.start.val('');
                    parent.end.val('');
                    refresh_pickers();
                });
                refresh_pickers();
            }

            refresh();
        },
        changed: function(){
            if (this.options.onChange){
                this.options.onChange(this);
            }
        }
    });

})(jQuery);

(function($) {
    // TODO: Use the title attr to link the picker, start and end components together or, even better, a fieldset
    $.widget("ui.download_button", {
        _create: function() {
            var obj = this.element;
            var $$ = this.obj = this.$$ = $(obj);
            var parent = this;
            var uuid = create_uuid();
            var frame = $('<iframe id="' + uuid + '" src="" style="display:none; visibility:hidden;"></iframe>');
            function refresh(){
                obj.button();
                parent.link = $$.find('a');
                parent.href = $$.find('a').attr('href')
                parent.link.attr('href', 'javascript:void(0);');
                frame.attr('src', parent.href);
                obj.click(function(){
                    if (!obj.hasClass('ui-state-disabled')){
                        obj.append(frame);
                        obj.addClass('ui-state-disabled');
                        function cleanup_download(){
                            obj.removeClass('ui-state-disabled');
                            $('#' + uuid).remove();
                        }
                        $('#' + uuid).load(function (){
                            cleanup_download();
                        });
//                        setTimeout(cleanup_download, 240000);
                    }
                });
            }
            refresh();
        }
    });

})(jQuery);

(function($) {
    $.widget("ui.feedback_button", {
        _create: function() {
            var obj = this.element;
            var $$ = this.obj = this.$$ = $(obj);
            var parent = this;

            var default_form = LIMBO.LOADER,
                current_div = null;

            function set_form(div, form_html){
                if (form_html == undefined){
                    form_html = parent.default_form;
                }
                current_div = div;
                current_div.html(parent.default_form);
                LIMBO.process(current_div);
                var form = current_div.find('form');
                form.ajaxForm({
                    data:data_dump("User Information"),
                    dataType:'json',
                    beforeSend: function(){
                        current_div.dialog('disable');
                    },
                    success:function(data){
                        current_div.dialog('enable');
                        if (data['success']) {
                            current_div.dialog('close');
                            LIMBO.messages.from_data(data);
                        } else {
                            set_form(current_div, $(data['form']));
                        }
                    }
                });
            }

            jQuery.ajax({
                url:LIMBO.URLS['feedback_form'],
                dataType:'json',
                success:function(data){
                    parent.default_form = data['form'];
                    if (current_div != null){
                        set_form(current_div);
                    }
                }
            });
            function get_feedback(){
                var div = LIMBO.make('#feedback_form', '<div id="feedback_form"></div>');
                set_form(div);
                div.dialog({
                            width: 600,
                            modal: true,
                            buttons: {
                                "Save": function() {
                                    div.find('form').submit();
                                },
                                Cancel: function() {
                                    $(this).dialog("close");
                                }
                            }
                });
            }

            $$.click(function(){
                get_feedback();
                return false;
            });
        }
    });

})(jQuery);

var LIMBO = window.LIMBO;

jQuery.fn.slugify = function(obj) {
    jQuery(this).data('origquery', this);
    jQuery(this).data('obj', jQuery(obj));
    var obj = jQuery(this).data('obj');
    if (obj == undefined){
        return;
    }
    obj.tracked = true;
    jQuery(this).keyup(function() {
        if (obj.tracked){
            var oquery = jQuery(this).data('origquery');
            var vals = [];
            jQuery(oquery).each(function (i) {
                vals[i] = (jQuery(this).val());
            });
            var slug = vals.join(' ').toLowerCase().replace(/\s+/g,'-').replace(/[^a-z0-9\-]/g,'');
            obj.val(slug);
        }
    });
    obj.keyup(function() {
        if (obj.val()) {
            obj.tracked = false;
        } else {
            obj.tracked = true;
        }
    });
    return this;
};

$(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});

function data_dump(message, url, line){
    if (url == undefined){
        url = window.location.href;
    }
    return {
        message:message,
        url:url,
        line:line,
        browser_codename:navigator.appCodeName,
        browser_appname:navigator.appName,
        browser_appversion:navigator.appVersion,
        browser_cookiesenabled:navigator.cookieEnabled,
        browser_platform:navigator.platform,
        browser_useragent:navigator.userAgent
    };
}

function errorHandler(message, url, line){
    /*
     * Log errors to server url: ERROR_URL
    */
    $.ajax({
        data:data_dump(message, url, line),
        dataType:'json',
        type:'GET',
        url:LIMBO.ERROR_URL,
        success:function(data, textStatus, jqXHR){
            if (LIMBO.messages != undefined){
                LIMBO.messages.from_data(data);
            }
        }
    });
    return true;
}

LIMBO.errorHandler = errorHandler;
window.onerror = LIMBO.errorHandler;

LIMBO.parse_date = function(d){
    if (d == ''){
        return null;
    }
    var dt = Date.parse(d);
    if (dt != null){
        return dt;
    }
    dt = Date.parse(d.split('.')[0]);
    if (dt != null){
            return dt;
        }
    return Date.parse(d.split(' ')[0]);
}

LIMBO.date_display = function(d){
    try {
        if (d.constructor != Date){
            d = LIMBO.parse_date(d);
        }
    } catch (e){
        return '';
    }
    var month = d.getMonth() + 1;
    var day = d.getDate();
    var year = d.getFullYear();
    return month + '/' + day + '/' + year;
}

LIMBO.date_span = function(start, end){
    start = LIMBO.date_display(start);
    end = LIMBO.date_display(end);
    var timespan = '';
    timespan += '<span class="start">' + start+ '</span> - ';
    timespan += '<span class="end">' + end+ '</span>';
    return timespan;
}

LIMBO.make = function(sel, html, append_to){
    // Create the object if length is 0, otherwise create jQuery object
    if (append_to == undefined){
        append_to = 'body';
    }
    if ($(sel).length == 0){
        $(append_to).append(html);
    }
    return $(sel);
};

LIMBO.absolute_url = function(params, href){
    if (!href){href=window.location.pathname;}
    for (var param in params){
        if (param.indexOf('http://') != -1){
            delete params[param];
        }
    }
    params = $.param(params, true);
    return href + '?' + params;
};

LIMBO.location = function(params, href){
    window.location = LIMBO.absolute_url(params, href);
};

$.extend({
    url_vars: function(){
        var vars = {}, hash;
        var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
        for(var i = 0; i < hashes.length; i++)
        {
            hash = hashes[i].split('=');
            // vars.push(hash[0]);
            vars[hash[0]] = hash[1];
        }
        return vars;
    },
    url_var: function(name){
        return $.url_vars()[name];
    }
});

LIMBO.stripe = function() {
//    $('tr.odd').addClass('ui-state-highlight');
//    $('tr.even').removeClass('ui-state-highlight');
};

function DateRange(obj){
    this.obj = obj;

}
LIMBO.DateRange = DateRange;


function Message(message, type, href, undo){
    var self = this;
    this.message = message;
    this.type = type;
    this.undo = undo;
    this.href = href;

    this.process = function(){
        this.undo_a = LIMBO.messages.container.find('a.ajax_undo[href="' + self.href + '"]');
        if (self.undo){
            self.undo_a.click(function(){
                $.ajax({
                    type:'delete',
                    url:self.href,
                    dataType:'json',
                    success:function(data){
                        LIMBO.messages.from_data(data);
                    }
                });
                self.undo();
                return false;
            })
        }
    }
}
LIMBO.Message = Message;

function Messages(){
    var msgs = this;
    this.pos = 0;
    this.msg_width = 600; //px

    this.__init__ = function(){
        this.btn_right = $('.msgR');
        this.btn_left = $('.msgL');
        this.buttons = $('.msgR, .msgL');

        this.btn_left.button().click(function(){
            msgs.left();
        });
        this.btn_right.button().click(function(){
            msgs.right();
        });
        this.refresh();
    };

    this.refresh = function(){
        this.messages = $('.messages .message');
        this.slider = $('.message_slider');
        this.container = $('.messages');
        this.wrapper = $('.messages_wrapper');
        this.slider.addClass('ui-corner-all').addClass('ui-state-active');

        if (this.length() != 0){
            this.messages.each(function(){
                $(this).addClass('ui-corner-all');
                var i = $(this).children('i');
                i.addClass('messages-s');
                if ($(this).hasClass('debug')){
                    i.addClass('messages-terminal');
                } else if ($(this).hasClass('info')){
                    i.addClass('messages-info');
                } else if ($(this).hasClass('success')){
                    i.addClass('messages-tick');
                } else if ($(this).hasClass('warning')){
                    i.addClass('messages-warning');
                } else if ($(this).hasClass('error')){
                    i.addClass('messages-error');
                }
            });
            this.resize();
        }
    };

    this.length = function(){
        return this.messages.length;
    };

    this.resize = function(){
        this.container.css('width', (this.length()*this.msg_width + 100) + 'px'); // Add buffer for ie
        this.reposition();
    };

    this.left = function(){
        this.buttons.removeClass('ui-state-disabled');
        if (this.pos > 0){
            this.pos -= 1;
        } else {
            this.pos = 0;
        }
        this.reposition();
    };

    this.message = function(){
        return $(this.messages[this.pos]);
    };

    this.right = function(){
        if (this.pos < this.length()-1){
            this.pos += 1;
        } else {
            this.pos = this.length()-1
        }
        this.reposition();
    };

    this.hide = function(){
        this.wrapper.fadeOut(1000);
    };

    this.show = function(){
        this.wrapper.fadeIn(1000);
    };

    this.reposition = function(){
        this.container.stop().animate({'left': -(this.pos*this.msg_width) + 'px'}, 1000, "easeOutCirc");
        this.buttons.removeClass('ui-state-disabled');
        if (this.length() == 1){
            this.buttons.addClass('ui-state-disabled');
        }
        else if (this.pos == 0){
            this.btn_left.addClass('ui-state-disabled');
        } else if (this.pos == this.length() - 1){
            this.btn_right.addClass('ui-state-disabled');
        }
        if (this.length() == 0){
            this.hide();
        } else if (this.length() == 1){
            this.show();
            this.buttons.hide();
        } else {
            this.show();
            this.buttons.show();
        }
        this.border_color(this.message().css('color'));
    };

    this.border_color = function(color){
        this.slider.stop()
            .animate({
                    borderBottomColor: color,
                    borderRightColor: color,
                    borderLeftColor: color,
                    borderTopColor: color}, 1000, "easeOutCirc");
    };

    this.append = function(message) {
        var html = '<span title="' + message['message'] + '" class="message ' + message['type'] + ' ui-corner-all"><span class="msg_icon"></span>' + message['message'] + '</span>';
        this.container.append(html);
        this.pos = this.length();
        this.refresh();
        message.process();
    };

    this.from_data = function(data, undo){
        if (data.message) {
                this.from_object(data.message, undo)
            }
    };

    this.from_object = function(message, undo){
        var msg = new Message(message.message, message.type, message.undo, undo);
        this.append(msg);
    };

    this.ajax_error = function(err){
        append('Failed to reach the server, please try again later.', 'error');
    };

    this.sync = function(){
        $.ajax({
            url:LIMBO.MESSAGE_SYNC,
            dataType:'json',
            success:function(data){
                $(data.messages).each(function(){
                    LIMBO.messages.from_object(this);
                });
            }
        });
    };

    this.error = function(msg){
        this.append(new Message(msg, 'error', undefined, undefined));
    };

    this.__init__();
}

LIMBO.Messages = Messages;

function ModalDialogs(){
    this._dialog = function(title, msg, cls){
        var id = "dialog-" + cls,
            dlg = LIMBO.make("#" + id, "<div id='" + id + "'></div>");
        dlg.html(msg)
            .dialog({
                modal: true,
                buttons: {
                    Ok: function() {
                        $( this ).dialog( "close" );
                    }
                },
                title:title
            });
    };

    this._ok_cancel_dialog = function(title, msg, callback, cls){
        var id = "dialog-" + cls,
          dlg = LIMBO.make("#" + id, "<div id='" + id + "'></div>");
        dlg.html(msg)
            .dialog({
                modal: true,
                buttons: {
                    Ok: function() {
                        callback($(this));
                        $( this ).dialog( "close" );
                   },
                    Cancel: function() {
                        $( this ).dialog( "close" );
                    }
                },
                title:title
            });
    };

    this.info = function(title, msg){
        var info_msg = "<p class='modal_msg'><span></span>" + msg + "</p>";
        return this._dialog(title, info_msg, 'info');
    };

    this.form = function(key) {
        var id = "dialog-form";
        if (key != undefined){
            id += '-' + key
        }
        LIMBO.make("#" + id, "<div id='" + id + "'></div>");
        return $('#' + id);
    };

    this.verify = function(title, msg, callback){
        var verify_msg = "<p class='modal_msg'><span></span>" + msg + "</p>";
        return this._ok_cancel_dialog(title, verify_msg, callback, 'verify');
    }

}

LIMBO.dialogs = new ModalDialogs();

LIMBO.not_implemented = function(){
    LIMBO.dialogs.info("Feature not implemented", "This feature has not yet been implemented. <br/>Please try again later.");
    return false;
};

function FormField(obj) {
    this.obj = obj;
    var parent;
    parent = this;
    this.__init__ = function() {
        this.id = obj.attr('id');
        var id = this.id;
        this.errors = $('.field_errors[name="' + id + '"]');
        this.help_sel = '.field_help[name="' + id + '"]';
        this.help = $(this.help_sel);

        this.refresh();
    };

    this.refresh = function() {
        if (this.obj.next().hasClass('ui-autocomplete-input')) {
            this.autocomplete = $(this.obj.next());
        } else {
            this.autocomplete = null;
        }
        if (this.errors.text()) {
            this.errors.css('display', 'block');
            this.obj.addClass('ui-state-error');
            if (this.autocomplete) {
                this.autocomplete.addClass('ui-state-error');
            }
        } else {
            this.errors.hide();
        }

        if (this.help.text()) {
            LIMBO.help_dialog.bind(this.obj, this.help.text(), ['info']);
            if (this.autocomplete) {
                LIMBO.help_dialog.bind(this.autocomplete, this.help.text(), ['info']);
            }
        }
    };

    this.__init__()
}
LIMBO.FormField = FormField;

function ContingentForm(field, href){
    this.field = field;
    this.form = field.parents('form');
    this.href = href;
    this.cform = LIMBO.LOADER;
    var parent = this;
    var dlg = LIMBO.dialogs.form(new Date().getTime());
    this.dialog = dlg;

    this.btn = "<button class='show_cform'>+</button>";
    var wrapper = this.field.parent();
    wrapper.append(this.btn);
    this.button = wrapper.find('.show_cform').button();
    this.button.click(function(){
        // Each contingent form gets a separate dialog
        parent.load_form();
        dlg.html(parent.cform);
        LIMBO.process(dlg);
        dlg.dialog({
            modal:true,
            minWidth:800,
            position:['center', 20],
            buttons:{
                    Save:function(){
                        // Submit form
                        parent.save();
                    },
                    Cancel: function(){
                        parent.save_state();
                        $(this).dialog('close');
                    }
                }
            });

        return false;
    });

    this._handle_data = function(data){
        LIMBO.messages.from_data(data);
        if (data.form){
            parent.cform = data.form;
            parent.repaint(this.dialog);
        }
        if (data.success == "True" || data.success == true){
            parent.process(data);
            this.dialog.dialog('close');
        }
    };

    this.load_form = function(){
        if (this.cform == LIMBO.LOADER){
            $.ajax({
                url:this.href,
                dataType:'json',
                success: function(data){
                    parent._handle_data(data);
                }
            });
        }
    };

    this.process = function(data){
        this.field.append('<option value="' + data.id + '">' + data.value + '</option>');
        this.field.combobox('set', data.value);
    };

    this.repaint = function(){
        var frm = $(this.cform);
        frm.find('.action_bar').remove();
        this.dialog.html(frm);
        LIMBO.process(this.dialog);
    };


    this.save_state = function(){
        // TODO: Save state so it has the same data when you reopen
    };

    this.save = function(){
        this.save_state(this.dialog);
        var options = {
            dataType:'json',
            beforeSubmit:function(){
                    parent.dialog.find('.ui-dialog-buttonset').addClass('ui-state-disabled');
            },
            success: function(data){
                parent.dialog.find('.ui-dialog-buttonset').removeClass('ui-state-disabled');
                parent._handle_data(data);
            }
        };

        // Ajax form submit
        this.dialog.find('form').ajaxSubmit(options);

    };

}
LIMBO.contingent_forms = {};

function Form(obj) {
    var parent = this;
    this.obj = this.$$ = obj;
    this.__init__= function(){
        this.form_errors = this.obj.find('.form_errors');
        this.form_error = this.obj.find('.form_errors li');
        this.field_errors = this.obj.find('.field_errors');
        this.field_help = this.obj.find('.field_help');
        this.meta = this.obj.find('.form_meta');
        this.refresh();
    };
    this.refresh = function(){
        obj.find('.range_picker').range_picker();
        this.form_errors.addClass('ui-state-error').addClass('ui-widget');
        this.form_error.addClass('ui-state-error-text').addClass('ui-widget');
        this.field_errors.addClass('ui-state-error')
                .addClass('ui-state-error-text')
                .addClass('ui-widget');
        var fields = [];
        this.fields = fields;
        this.field_errors.each(function(){
            var sel = '#' + $(this).attr('name');
            var field = new FormField($(sel));
            fields.push(field)
        });
        LIMBO.stripe();

        $('form input').addClass('ui-widget');
        if (this.meta){
            var prepopulated_fields = this.prepopulated_fields = {};
            this.meta.find('.prepopulated_fields').each(function(){
                    $(this).find('td').each(function(){
                        var key = $(this).find('.key').text();
                        var values = []
                        $(this).find('.value').each(function(){
                            var value = $(this).text();
                            values.push(value);
                            if (value != undefined && key != undefined){
                                if ($("#" + value) && $("#" + key)){
                                    $("#" + value).slugify("#" + key);
                                }
                            }
                        });
                        prepopulated_fields[key] = values;

                    });
            });

            var contingent_forms = this.contingent_forms = {};
            this.meta.find('.contingent_forms td a').each(function(){
                var field_id = $(this).text().trim(),
                    href = $(this).attr('href').trim();
                if (LIMBO.contingent_forms[field_id] != undefined){
                    contingent_forms[field_id] = LIMBO.contingent_forms[field_id];
                } else {
                    var field = $('#' + field_id);
                    var cform = new ContingentForm(field, href);
                    contingent_forms[field_id] = cform;
                    LIMBO.contingent_forms[field_id] = cform;

                }
            });
        }
    };

    this.__init__();
};

function Forms(){
    this.forms = [];
    var parent = this;
    this.__init__= function(){
        this.form_errors = $('.form_errors');
        this.form_error = $('.form_errors li');
        this.field_errors = $('.field_errors');
        this.field_help = $('.field_help');
        this.meta = $('.form_meta');
        this.refresh();
    };

    this.refresh = function(){
        this.forms = [];
        $('form').each(function(){
            parent.forms.push(new Form($(this)));
        });

    };
    this.__init__();
}

function HelpDialog(){
    if ($(document).find('#floatingMessage').length==0) {
        $('body').append("<div id='floatingMessage'></div>");
    }
    this.obj = $('#floatingMessage');
    var floating_msg = this.obj;
    floating_msg.addClass('ui-corner-all');

    this.bind = function(obj, html, classes){
        obj.hover(
            function(){ // Hover in
                floating_msg.html(html);
                obj.mousemove(function(e){
                    floating_msg.css({
                        top: e.pageY + 15 + 'px',
                        left: e.pageX+ 5 + 'px'
                    });
                });
                if (classes){
                    for (var i in classes){
                        floating_msg.addClass(classes[i]);
                    }
                }
                floating_msg.removeClass('hidden').addClass('visible');
            },
            function(){ //Hover out
                floating_msg.removeClass('visible').addClass('hidden').html('');
                if (classes){
                    for (var i in classes){
                        floating_msg.removeClass(classes[i]);
                    }
                }
            }
        );
    }

}

function Buttons(){
    this.remove = function(obj, onSuccess, onError, msg, title){
        var a = obj.children('a'),
            href = a.attr('href');
        if (!msg){
            msg = '<p>Are you sure you want to remove this?</p>';
        }
        if (!title){
            title = 'Delete Verification';
        }
        a.attr('href', '#');
        function submit_remove(){
            var obj = $(this),
                dlg = LIMBO.dialogs.verify("");
            dlg.html(msg);
            dlg.dialog({
                modal:true,
                title:title,
                buttons:{
                    Delete:function(){
                        $.ajax({
                            url:href,
                            type:'post',
                            dataType:'json',
                            success: function(data){
                                LIMBO.messages.from_data(data);
                                if (onSuccess){
                                    onSuccess(obj, data);
                                }
                            },
                            error: function(data){
                                if (onError){
                                    onError(obj, data);
                                }
                            }
                        });
                        $(this).dialog('close');
                    },
                    Cancel:function(){
                        $(this).dialog('close');
                    }
                }
            });

            return false;
        }

        a.click(submit_remove);
    }
}

function ActionBars(sel){
    if (sel == undefined || sel == null){
        sel = '.action_bar';
    }
    this.sel = sel;

    this.beforeSend = function(obj){
        if (obj == undefined){
            obj= $(this.sel);
        }
        obj.addClass('ui-state-disabled');
        obj.append(LIMBO['LOADER']);
    };

    this.success = function(obj){
        if (obj == undefined){
            obj= $(this.sel);
        }
        obj.removeClass('ui-state-disabled');
        obj.find('img.loader').remove();
    }
}
LIMBO.action_bars = new ActionBars(null);


LIMBO.ajaxForm = function(form, target){
    var options = {
        beforeSend:function(){
            LIMBO.action_bars.beforeSend(form.find('.action_bars'));
        },
        success: function(data){
            LIMBO.messages.sync();
            LIMBO.messages.from_data(data);
            LIMBO.action_bars.success(form.find('.action_bars'));
            var id = form.attr('id'),
                new_form = $(data).find('#' + id);
            if (new_form.length != 0){
                LIMBO.process($(this));
            }
        },
        error: function(err){
            LIMBO.messages.sync();
            LIMBO.messages.append(new Message("There was an error processing your request. Please try again later.", "error", null, null));
        }
    };
    if (target != undefined){
        options['target'] = target;
    }

    form.ajaxForm(options);
};

function ModalButton(obj){
    var $$ = this.obj = this.$$ = obj;
    var parent = this;
//    modal_button
    this.content = obj.next();
    obj.button().click(function(){
        var dlg_id = obj.attr('id') + '_dlg';
        LIMBO.dialogs.info(parent.content.attr('title'), parent.content.html())
    });
}

LIMBO.modal_buttons = [];
function process_modal_buttons(obj){
    if (obj == undefined){
        obj = $('body');
    }
    obj.find('.modal_button').each(function(i, e){
        LIMBO.modal_buttons.push(new ModalButton($(e)));
    });
};

function ButtonForm(obj){
    var parent = this;
    this.button = obj.find('button').button();
    this.button_html = this.button.html();
    $(obj).ajaxForm({
        url: parent.source,
        beforeSubmit: function(){
            parent.button.html(LIMBO.LOADING);
            },
        success: function(data){
            obj.html(data);
            LIMBO.process(obj);
        },
        error: function(data){
            parent.button.html(this.button_html);
            LIMBO.messages.error("Update failed.  Please try again later.");
        }
    });
}

LIMBO.form_buttons = [];
function process_button_forms(obj){
    if (obj == undefined){
        obj = $('body');
    }
    obj.find('form.button_form').each(function(i, e){
        LIMBO.form_buttons.push(new ButtonForm($(e)));
    });
    if (obj.hasClass('button_form')){
        LIMBO.form_buttons.push(new ButtonForm(obj));
    }
}

function Paginator(obj){
    this.obj = obj;
    var self = this;
    this.__init__ = function(){
        this.pages = this.obj.find('.paginate-pages');
        this.first = this.obj.find('.paginate-first');
        this.previous = this.obj.find('.paginate-previous');
        this.current = this.obj.find('.paginate-current');
        this.links = this.obj.find('.paginate-link');
        this.next = this.obj.find('.paginate-next');
        this.last = this.obj.find('.paginate-last');
        this.refresh();
    };

    this.refresh = function(){
        this.pages.button();
        this.first.button();
        this.previous.button();
        this.current.button().addClass('ui-state-disabled');
        this.links.button();
        this.next.button();
        this.last.button();

        this.n_pages = parseInt(this.pages.text());
        this.pages.click(function(){
            self.jumpToPage()
        })
    };

    this.jumpToPage = function(){
        var pages = this.n_pages,
            page = prompt("Enter a number between 1 and " + pages + " to jump to that page", "");
        if (page != undefined)
        {
                page = parseInt(page, 10);
                if (!isNaN(page) && page > 0 && page <= pages)
                {
                        window.location.href = "?page=" + page;
                }
        }
    };
    this.__init__();
}

function Paginators(){
    this.paginators = [];
    var self = this;
    $('.paginator').each(function(){
        self.paginators.push(new Paginator($(this)));
    });
}

var _preprocess = [];
LIMBO.preprocess = function(c){
    _preprocess.push(c);
};

function fullscreen(obj, content){
    var width = $(window).width();
    var height = $(window).height();
    var fsd = LIMBO.make('#full_screen_div', "<div id='full_screen_div'></div>");
    if (content == undefined){
        content = obj.next('div');
    }
    fsd.html(content.html());
    fsd.dialog({
        modal:true,
        width:width - 25,
        height:height - 25,
        position:['left', 'top'],
        buttons: {
            Close: function(){
                $(this).dialog('close');
            }
        }
            });
}

function process_fullscreen(){
    $('.fullscreen_btn').click(function(){
        fullscreen($(this));
        return false;
    }).button();
}

LIMBO.process = function(obj){
    if (obj == undefined){
        obj= $('body');
    }
    for (var i in _preprocess){
        _preprocess[i]();
    }
    obj.find('.action_bar button, .action_bar input').button();
    obj.find('form input').addClass('ui-widget').addClass('ui-widget-content');
    obj.find('.buttonset').buttonset();
    obj.find('.date input').datepicker();
    obj.find('.datepicker').datepicker();
    obj.find('.timepicker').timepicker();
    obj.find('.autoresize').autoResize().addClass('ui-widget').addClass('ui-widget-content');
    obj.find('.autocomplete select').combobox();
    obj.find('select.combobox').combobox();
    obj.find('select.multiselect').multiselect();
    obj.find('.link_button').button();
    obj.find('.download_button').download_button();
    obj.find('.accordion').accordion({
                header: "h2",
                autoHeight: false,
                navigation: true
                });
    obj.find('.accordion_collapsible').accordion({
                header: "h2",
                autoHeight: false,
                navigation: true,
                collapsible:true
                });
    obj.find('form.collapsible').accordion({
                header: "fieldset legend",
                autoHeight: false,
                navigation: true,
                collapsible:true
                });
    obj.find('table.subreport').addClass('datatable');
    obj.find('.datatable').each(function(){
        var args = {
                "bJQueryUI": true,
                "iDisplayLength": 25,
                "sPaginationType": "full_numbers",
                "bStateSave":true
            },
            hiddens = [];
        $(this).find('thead th').each(function(index){
            var header = $(this).html().trim();
            if (header == '__aaSortingFixed__'){
                if (args['aaSortingFixed'] == undefined){
                    args['aaSortingFixed'] = [];
                }
                args['aaSortingFixed'].push([index, 'asc']);
                hiddens.push(index);
            }
        });

        if (hiddens.length > 0){
            args['aoColumnDefs'] = [{'bVisible':false, "aTargets":hiddens}];
        }
        // You don't want to reinitialize it so remove datatable
        $(this).dataTable(args).removeClass('datatable');
        });

    LIMBO.stripe();
    LIMBO.forms.refresh();
    obj.find('.errorlist').addClass("ui-state-error").addClass("ui-corner-all");
    obj.find('.ajaxform').each(function(){
        LIMBO.ajaxForm($(this));
    });
    obj.find(".media").media();
    obj.find('div.media').css('margin', 'auto');
//    process_fullscreen(obj);
    process_random_generators(obj);
    process_dashboards(obj);
    process_modal_buttons(obj);
    process_button_forms(obj);

    obj.find('.ui-report').each(function(index, ele){
        var id = $(ele).attr('id');
        if (LIMBO.Reports[id] == undefined){
            LIMBO.Reports[id] = new Report( $(ele) );
        }
    });

    obj.find('.toggle_section').each(function(i, obj){
        var button = $(obj).children('button'),
            section = button.next();
        button.button().click(function(){
            section.toggle();
            return false;
        });
        if ($(this).hasClass('toggle_on_load')){
            section.toggle();
        }
        section.addClass('toggle_section_content ui-widget ui-widget-content ui-corner-all');
    })
};

function Preloader(){
    this.data = {};
    this.ajaxOptions = {
        url:window.location.href
    };
    var self = this;

    this.expired = function(last_load){
        today=new Date();
        var minute=1000*60;
//      var minute = 1000;
        return Math.ceil((today.getTime() - last_load.getTime()) / (minute * 5)) > 1;
    };

    this.reload = function(options){
        if (!options){
            options = {};
        }
        var ajaxOptions = $.extend({}, this.ajaxOptions, options);
        $.ajax(ajaxOptions);
    }
}

LIMBO.preloader = new Preloader();

function DataTablesCallBack(callback){
    this.fn = this;
    this.call = callback;
}

function ServerDataTable(sel) {
    var parent = this;
    this.sel = sel;
    var ele = $(sel);
    var table = ele.find('table:first');
    var source = this.source = ele.find('.server_table_config a.tablesource')[0].getAttribute('href');
    this.advanced_search = $("<div class='dataTables_adv_filter'></div>")
    this.ele = ele;
    var $$ = this.$$ = $(ele);
    this.columns = {};
    this.rcolumns = {};
    this.inline_data = {};

    this.aoColumns = [];
    this.$$.find('ol.col_attrs li').each(function(index, e){
        try {
            var d = JSON.parse($(e).html());
            parent.aoColumns.push(d);
            parent.columns[index] = $(e).attr('title');
            parent.rcolumns[$(e).attr('title')] = index;
        } catch (e){
            console.log(e);
        }
    });
    this.callbacks = new Array();

    this.query_data = function (aoData){
        var data = {}
        if (aoData != undefined){
            for (var key in aoData){
                var o = aoData[key];
                data[o.name] = o.value;
            }
        }
        for (var key in LIMBO.GET){
            data[key] = LIMBO.GET[key];
        }
        var tdata = $.param(data, true);
        tdata += '&' + parent.advanced_search.find('input, select, textarea').serialize();
        console.log(tdata);
        return tdata;
    }

    var tbl_args = {
        "bProcessing": true,
        "bServerSide": true,
        "sAjaxSource": source,
        "bJQueryUI": true,
        "iDisplayLength": 25,
        "sPaginationType": "full_numbers",
        "sSearch": "Search all:",
        "bStateSave":true,
        "fnServerData": function ( sSource, aoData, fnCallback ) {
            var data = parent.query_data(aoData);
            $.ajax({
                url: sSource,
                dataType: 'json',
                data: data,
                success: function(json){
                    fnCallback(json)
                }
            });
        }
    };

    if (this.aoColumns.length != 0){
        tbl_args["aoColumns"] = this.aoColumns;
    }

    var oTable = $(table).dataTable( tbl_args );

    var oSettings = oTable.fnSettings();
    this.oSettings = oSettings;
    this.oServerData = oSettings.fnServerData;

    function setup_forms(){
        this.editable = false;
        if ($$.find(".action_bar")){
            this.editable = true;
            this.form = ele.find('form');
            this.form_obj = $(this.form);
            this.form_obj.ajaxForm({
                    url: parent.source,
                    data: parent.query_data(),
                    beforeSubmit: function(){
                        oTable.oApi._fnProcessingDisplay(oTable.fnSettings(), true);
                        },
                    success: function(data){
                        oTable.oApi._fnProcessingDisplay(oTable.fnSettings(), false);
                        LIMBO.messages.from_data(data);
                        if (data.success){
                            oTable.fnDraw();
                        } else {
                            alert (data.errors);
                        }
                    },
                    dataType:'json'
                    });
        }
    }

    function individual_filters() {

        parent.filters.keyup( function () {
            /* Filter on the column (the index) of this element */
            parent.oTable.fnFilter( this.value, parent.filters.index(this) );
        } );

        parent.filters.change( function () {
            /* Filter on the column (the index) of this element */
            parent.oTable.fnFilter( this.value, parent.filters.index(this) );
        } );

        /*
         * Support functions to provide a little bit of 'user friendlyness' to the textboxes in
         * the footer
         */
        parent.filters.each( function (i) {
            parent.asInitVals[i] = this.value;
            $(this).addClass("search_init");
        } );

        parent.filters.focus( function () {
            if ( $(this).hasClass("search_init") )
            {
                $(this).removeClass("search_init");
                this.value = "";
            }
        } );

        parent.filters.blur( function() {
            if ( this.value == "" ) {
                $(this).addClass("search_init");
                this.value = parent.asInitVals[parent.filters.index(this)];
            }
        } );

        // Reload data from saved state
        if (parent.oSettings.oLoadedState != null && parent.oSettings.oLoadedState['aaSearchCols'] != undefined){
            var pSearch = parent.oSettings.oLoadedState['aaSearchCols'];
            for (var index in parent.columns){
                parent.filters.each(function(){
                    if ($(this).attr('title') == parent.columns[index] && pSearch[index] != undefined){
                        var val = pSearch[index][0];
                        if (val != "" && val!= null && val != undefined){
                            $(this).val(val);
                            $(this).removeClass("search_init");
                        }
                    }
                });
            }
        }
    }

    function table_callbacks(settings){
            // Just a pass through to call all methods in the parent
            for (var index in parent.callbacks){
                parent.callbacks[index](settings);
            }
            LIMBO.process(parent.table);
        }

    function setup_menu() {
        var menu_html = parent.config.find('.col_menu');
        parent.ele.find(".dataTables_filter").append(menu_html);
        parent.menu = parent.ele.find(".dataTables_filter .col_menu");
        parent.menu.button();
        parent.menu_cols = parent.config.find('.col_menu_html');
        var col_menu_html = parent.menu_cols.html();
        var menu = parent.fgmenu = parent.menu.fgmenu({
                content: col_menu_html,
                positionOpts: {
                    posX: 'left',
                    posY: 'bottom',
                    offsetY:2,
                    directionH:'left'},
                showSpeed: 300,
                linkToFront: true
            });
        menu.container.find('a').each(function(){
            function update_disabled(obj){
                var col = parent.rcolumns[obj.attr('title')],
                    bVis;
                if (oTable.fnSettings().aoColumns && oTable.fnSettings().aoColumns[col]){
                    bVis = oTable.fnSettings().aoColumns[col].bVisible;
                } else {
                    bVis = true;
                }
                if (bVis){
                    obj.parent().removeClass("ui-state-disabled");
                } else {
                    obj.parent().addClass("ui-state-disabled");
                }
            }
            $(this).click(function(){
                var col = parent.rcolumns[$(this).attr('title')],
                    bVis;
                if (oTable.fnSettings().aoColumns && oTable.fnSettings().aoColumns[col]){
                    bVis = oTable.fnSettings().aoColumns[col].bVisible;
                } else {
                    bVis = true;
                }
                var newVis = bVis ? false : true;
                oTable.fnSetColumnVis( col, newVis);
                update_disabled($(this));
                return false;
           });
            update_disabled($(this));
        });
    }

    function fnFormatDetails ( url, row ){
        if (parent.inline_data[url]){
            return parent.inline_data[url];
        }
        $.ajax({
            url: url,
            cache:true,
            success: function(data){
                var new_row = oTable.fnOpen( row[0], data, 'details ui-widget ui-widget-content' );
                LIMBO.process($(new_row));
                parent.inline_data[url] = data;
            }
        });
        return LIMBO.LOADER;
    }

    function setup_inlines(){
        parent.ele.find('.inline_row').click(function(){
            var c = $(this),
                row = c.parents('tr'),
                url = c.attr('href'),
                cls = 'details_open';
            try {
                if (c.hasClass(cls)){
                    oTable.fnClose( row[0] );
                    c.removeClass(cls);
                } else {
                    var new_row = oTable.fnOpen( row[0], fnFormatDetails(url, row), 'details ui-widget ui-widget-content' );
                    new_row = $(new_row);
                    LIMBO.process(new_row);
                    LIMBO._c = row;
                    c.addClass(cls);
                }
            } catch (e) { console.log(e);
            } finally {

            }
            return false;
        });
    }
    this.callbacks.push(setup_inlines);

    function setup_advanced_search(){
        var adv_search_config = parent.config.find('.search_form');
        var adv_search = parent.advanced_search;
        if (adv_search_config.length > 0){
            adv_search.append(adv_search_config.html());
            adv_search.insertAfter(ele.find('.dataTables_filter'));
            // Add search button
            var adv_search_btn = parent.advanced_search_btn = $('<button class="dataTables_adv_filter_btn"><span class="ui-icon ui-icon-search"></span></button>');
            adv_search_btn.insertBefore(parent.menu).button().click(function(){
                adv_search.toggle();
                return false;
            });
            adv_search.find('input, select, textarea').change(function(){
                parent.process();
            });
            adv_search_config.remove();
        }
        adv_search.hide().addClass('ui-widget ui-widget-content ui-corner-all');
    }

    this.process = function(){
        oTable.fnDraw();
    };

    /* This handles all callback stuff and makes it easier to
     * just pass a function in to be called upon draw of the table.
    */
    this.add_callback = function(callback){
        this.callbacks.push(callback);
    };

    var call_all = new DataTablesCallBack(table_callbacks);
    this.call_all = call_all;
    oSettings.aoDrawCallback.push(call_all);

    this.ele = ele;
    this.table = table;
    this.oTable = oTable;
    this.asInitVals = new Array();
    this.filters = parent.$$.find("tfoot input, tfoot select");
    individual_filters();
    this.config = this.$$.find('.server_table_config');
    this._config_html = this.config.html();
    setup_menu();
    setup_inlines();
    setup_advanced_search();
    setup_forms();
//    this.config.remove();
}

function process_server_data_tables(sel){
    if (!sel){
        sel = '.server_datatable';
    }
    if (LIMBO.server_tables == undefined){
        LIMBO.server_tables = new Object();
    }
    var obj = $(sel);
    obj.each(function(index, element){
        var e = $(element);
        var tble = e.find('table');
        if (LIMBO.server_tables[tble.attr('id')] == undefined){
            LIMBO.server_tables[tble.attr('id')] = new ServerDataTable(element);
        }
    });
}
_preprocess.push(process_server_data_tables);

LIMBO.dashboards = [];
function Dashboard(obj){
    var $$ = this.obj = this.$$ = obj;
    this.wrapper = obj.parent();
    var parent = this;
    var url = this.url =  obj.find('a.dlink').attr('href').trim();
    var ts_label = "<label>Time Span:</label>";

    function handle_data(data){
        for (key in data){
            obj.find('.' + key + ' .dval').html(data[key]);
        }
        var timespan = ts_label + LIMBO.date_span(data['start'], data['end']);
        parent.timespan.html(timespan);
        return false;
    }
    this.handle_data = handle_data;

    this.refresh = function(){
        this.values.html(LIMBO.LOADER);
        this.timespan.html(ts_label + LIMBO.LOADER);
        if (parent.form){
            parent.form.submit();
        } else {
            $.ajax({
                url:url,
                dataType:'json',
                beforeSend:function(){
                    parent.refresh_btn.addClass('ui-state-disabled');
                },
                success:function(data){
                    parent.refresh_btn.removeClass('ui-state-disabled');
                    handle_data(data);
                }
            });
        }
    };

    function setup_form(){
        obj.append(LIMBO.DASHBOARD_FILTER_FORM);
        parent.refresh_btn = obj.find('.drefresh');
        parent.filter_btn = obj.find('.dfilter');
        parent.filter_panel = obj.find('.dfilters');
        parent.values = obj.find('.dval');
        parent.actionbar = obj.find('.action_bar');
        parent.timespan = obj.find('.dtimespan');
        var form = parent.form = obj.find('form');
        parent.form.attr('action', url);
        parent.default_range = $$.find('.default_range');
        if (parent.default_range.length != 0){
            var dstart = LIMBO.parse_date(parent.default_range.find('.start').text()),
                dend = LIMBO.parse_date(parent.default_range.find('.end').text());
            parent.form.find('.datepicker[name=start]').val(LIMBO.date_display(dstart));
            parent.form.find('.datepicker[name=end]').val(LIMBO.date_display(dend));
            var picker = parent.form.find('.range_picker');
            picker.find('input[checked=checked]').attr('checked', '');
        }
        form.ajaxForm({
            dataType:'json',
            beforeSend:function(){
                LIMBO.action_bars.beforeSend(parent.actionbar);
                parent.values.html(LIMBO.LOADER);
                parent.timespan.html(ts_label + LIMBO.LOADER);
                parent.obj.addClass('ui-state-disabled');
            },
            success: function(data){
                parent.obj.removeClass('ui-state-disabled');
                LIMBO.messages.from_data(data);
                LIMBO.action_bars.success(parent.actionbar);
                parent.handle_data(data);
            }
        });

        parent.refresh_btn.click(function(){
            parent.refresh();
            return false;
        });

        parent.filter_btn.click(function(){
            parent.filter_panel.toggle();
            return false;
        });
    }
    setup_form();
    LIMBO.process(obj);
    this.refresh();

}

function process_dashboards(obj){
    obj.find('.dashboard').each(function() {
        LIMBO.dashboards.push(new Dashboard($(this)));
    });
}

function RandomGenerator(obj){
    var $$ = this.obj = this.$$ = obj;
    this.wrapper = obj.parent();
    var parent = this,
        url = LIMBO.URLS['random_string'];
    if (this.wrapper.find('.generate_random').length == 0){
        this.btn = "<button class='generate_random'>Generate</button>";
        this.wrapper.append(this.btn);
        this.button = this.wrapper.find('.generate_random');
            this.button.button().click(function(){
            parent.generate();
            return false;
        });
    }

    this.generate = function(){
        data = {}
        if ($$.attr('maxlength')){
            data['max_length'] = $$.attr('maxlength');
        }
        $.ajax({
            data:data,
            dataType:'json',
            url:url,
            success: function(data){
                $$.val(data['0']);
            }
        });
    }

}
LIMBO.random_generators = {};

function process_random_generators(){
    $('.random_generator').each(function(){
        var id = $(this).attr('id');
        LIMBO.random_generators[id] = new RandomGenerator($(this));
    });
}

$(function(){
    LIMBO.background_image = $('body').css('background-image');
    LIMBO.server_tables = new Object();
    LIMBO.help_dialog = new HelpDialog();
    LIMBO.paginators = new Paginators();
    $('#user_info').fgmenu({
            content: $('#user_menu').html(),
            positionOpts: {
                posX: 'left',
                posY: 'bottom',
                offsetY:2,
                directionH:'left'},
            showSpeed: 300,
            linkToFront: true
        });
    LIMBO.messages = new Messages();
    LIMBO.forms = new Forms();
    LIMBO.buttons = new Buttons();
    LIMBO.stripe();
    LIMBO.process();

    $( "#tabs" ).tabs({
        ajaxOptions: {
            error: function( xhr, status, index, anchor ) {
                $( anchor.hash ).html(
                    "Couldn't load this tab. We'll try to fix this as soon as possible. ");
            }
        },
        cache: True,
        select: function(event, ui) {
            window.location = ui.tab.href;
            process_server_data_tables(null);
        },
        create: function () {
            LIMBO.process($(this));
        },
        load: function () {
            LIMBO.process($(this));
        }
    });

   $('.action_list li').click(function(){
       if ($(this).find('a').attr('href') == '#'){
           var message = new LIMBO.Message("Yea, that's still to come.");
           LIMBO.messages.append(message);
           return false;
       }
   });
});

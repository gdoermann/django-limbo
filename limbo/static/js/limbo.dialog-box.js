/*
This widget will create a standard inline dialog box
Example:
<div class='dialog-box'>
    <h3>Alerts</h3>
    <div>
        <ol>
            <li>Alert 1</li>
            <li>Alert 2</li>
            <li>Alert 3</li>
        </ol>
    </div>
</div>

*/

(function($) {
    $.widget("ui.dialogbox", {
        options: {
            header:'h3'
        },
        _create: function() {
            var self = this;
            var element = this.element;
            var header = $(element).find(this.options.header);
            var body = header.next();
            var template = $("<div class='dialogbox_header'></div><div class='dialogbox_body'></div><div class='dialogbox_footer'>&nbsp;</div>");
            element.append(template);
            var template_header = element.children('.dialogbox_header');
            template_header.append(header).addClass('fg-toolbar ui-toolbar ui-widget-header ui-corner-tl ui-corner-tr ui-helper-clearfix');
            template_header.children(this.options.header).css('text-align', 'center');
            element.children('.dialogbox_body').append(body).addClass('ui-widget-content');
            element.children('.dialogbox_footer').addClass('fg-toolbar ui-toolbar ui-widget-header ui-corner-bl ui-corner-br ui-helper-clearfix');

        }
    });

})(jQuery);

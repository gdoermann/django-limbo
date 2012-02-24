LIMBO = window.LIMBO;

function BaseDataTable(sel){
    this.setup(sel);
}

BaseDataTable.method("setup", function(sel){
    if (sel == undefined){
        return;
    }
    var parent = this;
    this.sel = sel;
    this.ele = $(sel);
    this.table = this.ele.find('table:first');
    this.advanced_search = $("<div class='dataTables_adv_filter'></div>");
    this.$$ = $(this.ele);
    this.columns = {};
    this.rcolumns = {};
    this.inline_data = {};
    if (LIMBO.static_tables[this.table.attr('id')] != undefined || LIMBO.server_tables[this.table.attr('id')] != undefined){
        throw "Datatable already initialized!";
    }

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

    this.table_callbacks = function (settings){
        // Just a pass through to call all methods in the parent
        for (var index in parent.callbacks){
            parent.callbacks[index](settings, parent);
        }
        LIMBO.process(parent.table.find('td'), false);
    };
});

BaseDataTable.method("get_table_args", function(){
    return {
        "bProcessing": true,
        'bDestroy':true,
        "bJQueryUI": true,
        "iDisplayLength": 50,
        "sPaginationType": "full_numbers",
        "sSearch": "Search all:",
        "bStateSave":true,
        "sScrollX": "100%"
    };
});

BaseDataTable.method("init", function init(){
    this.ele.find('input,select').css('width', '5px').addClass('datatable_input');
    var tbl_args = this.get_table_args();
    var oTable = $(this.table).dataTable( tbl_args );

    var oSettings = oTable.fnSettings();
    this.ele.find('.datatable_input').css('width', '100%');

    this.tbl_args = tbl_args;
    this.oTable = oTable;
    this.oSettings = oSettings;
    this.oServerData = oSettings.fnServerData;
    this.config = this.$$.find('.server_table_config');
    this._config_html = this.config.html();
    this.setup_callbacks();

    this.individual_filters();
    this.setup_menu();
    this.setup_inlines();
    this.setup_advanced_search();
    this.setup_forms();
    this.setup_new_form();
//    this.config.remove();

});

BaseDataTable.method("filter_index", function(input){
    var parent = this;
    var vindex = parent.filters.index(input),
        visibles = 0;
    for (var index in parent.oSettings.aoColumns){
        var col = parent.oSettings.aoColumns[index];
        if (col.bVisible){
            visibles += 1;
        }
        if (visibles == vindex+1){
            return col.iDataSort;
        }
    }
    return vindex;
});

BaseDataTable.method("get_source", function(){
    return this.source;
});

BaseDataTable.method("setup_forms", function(){
    var oTable = this.oTable;
    var parent = this;
    var $$ = this.$$;
    this.editable = false;
    if ($$.find(".action_bar")){
        this.editable = true;
        this.form = parent.ele.find('form');
        this.form_obj = $(this.form);
        this.form_obj.ajaxForm({
            url: parent.get_source(),
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
});

BaseDataTable.method("individual_filters", function () {
    this.asInitVals = new Array();
    var parent = this;
    parent.filters = parent.$$.find("tfoot input, tfoot select");
    parent.filters.each( function (i) {
        if (!$(this).attr('id')){
            $(this).attr('id', create_uuid());
        }
        if (!$(this).hasClass('initialized')){
            parent.asInitVals[$(this).attr('id')] = this.value;
            $(this).addClass("search_init initialized ui-widget ui-widget-content");
        }
        $(this).keyup( function () {
            /* Filter on the column (the index) of this element */
            parent.oTable.fnFilter( this.value, parent.filter_index(this) );
        } );

        $(this).change( function () {
            /* Filter on the column (the index) of this element */
            parent.oTable.fnFilter( this.value, parent.filter_index(this) );
        } );

        $(this).focus( function () {
            if ( $(this).hasClass("search_init") )
            {
                $(this).removeClass("search_init");
                this.value = "";
            }
        } );

        $(this).blur( function() {
            if ( this.value == "" ) {
                $(this).addClass("search_init");
                this.value = parent.asInitVals[$(this).attr('id')];
            }
        } );
    });
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
});

BaseDataTable.method("setup_menu", function () {
    var parent = this;
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
            if (parent.oTable.fnSettings().aoColumns && parent.oTable.fnSettings().aoColumns[col]){
                bVis = parent.oTable.fnSettings().aoColumns[col].bVisible;
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
            if (parent.oTable.fnSettings().aoColumns && parent.oTable.fnSettings().aoColumns[col]){
                bVis = parent.oTable.fnSettings().aoColumns[col].bVisible;
            } else {
                bVis = true;
            }
            var newVis = bVis ? false : true;
            parent.oTable.fnSetColumnVis( col, newVis);
            update_disabled($(this));
            parent.individual_filters();
            parent.table.find('select, input').css('width','100%');
            return false;
        });
        update_disabled($(this));
    });
});


BaseDataTable.method("fnFormatDetails", function ( url, row ){
    var parent = this;
    $.ajax({
        url: url,
        cache:true,
        success: function(data){
            var new_row = parent.oTable.fnOpen( row[0], data, 'details ui-widget ui-widget-content' );
            LIMBO.process($(new_row));
            parent.inline_data[url] = data;
        }
    });
    return LIMBO.LOADER;
});

BaseDataTable.method("setup_inlines", function (settings, parent){
    if (parent == undefined){
        parent = this;
    }
    parent.ele.find('.inline_row').click(function(){
        var c = $(this),
            row = c.parents('tr'),
            url = c.attr('href'),
            cls = 'details_open';
        try {
            if (c.hasClass(cls)){
                parent.oTable.fnClose( row[0] );
                c.removeClass(cls);
            } else {
                var new_row = parent.oTable.fnOpen( row[0], parent.fnFormatDetails(url, row), 'details ui-widget ui-widget-content' );
                new_row = $(new_row);
                LIMBO.process(new_row);
                c.addClass(cls);
            }
        } catch (e) { console.log(e);
        } finally {

        }
        return false;
    });
});

BaseDataTable.method("setup_callbacks", function (){
    this.callbacks.push(this.setup_inlines);
    this.call_all = {
        'fn':this.table_callbacks,
        'sName':'CallCall'
    }
    this.oSettings.aoDrawCallback.push(this.call_all);
});

BaseDataTable.method("add_callback", function(callback){
    /* This handles all callback stuff and makes it easier to
     * just pass a function in to be called upon draw of the table.
     */
    this.callbacks.push(callback);
});

BaseDataTable.method("process", function(callback){
    this.oTable.fnDraw();
    if (callback != undefined){
        callback();
    }
});

BaseDataTable.method("setup_advanced_search",  function (){
    var parent = this;
    var adv_search_config = parent.config.find('.search_form');
    var adv_search = parent.advanced_search;
    if (adv_search_config.length > 0){
        adv_search.append(adv_search_config.html());
        adv_search.insertAfter(parent.ele.find('.dataTables_filter'));
        // Add search button
        var adv_search_btn = parent.advanced_search_btn = $('<button class="dataTables_adv_filter_btn"><span class="ui-icon ui-icon-search"></span></button>');
        adv_search_btn.insertBefore(parent.menu).button().click(function(){
            adv_search.toggle();
            return false;
        });
        adv_search.find('input[type=checkbox], input[type=radio]').change(function(){
            parent.process();
        });
        var changed_elements = {};

        function reset_element(e){
            changed_elements[$(e).attr('id')] = $(e).val();
        }

        function register_element(e){
            if (changed_elements[$(e).attr('id')] && changed_elements[$(e).attr('id')] != $(e).val()){
                parent.process();
            }
            reset_element(e);
        }

        function check_element_changed(e){
            if (changed_elements[$(e).attr('id')] != $(e).val()){
                parent.process();
                reset_element(e);
            }
        }

        adv_search.find('input, select, textarea').change(function(){
            register_element(this);
        });

        adv_search.find('input.datepicker').datepicker( "option" , 'onSelect', function(){
            check_element_changed(this);
        });

        adv_search.find('input, select, textarea').blur(function(){
            check_element_changed(this);
        });
        adv_search_config.remove();
    }
    adv_search.hide().addClass('ui-widget ui-widget-content ui-corner-all');
});

BaseDataTable.method("setup_new_form", function(){
    var parent = this;
    var form_id = 'tableadd-' + parent.table.attr('id');
    var new_form_link = $(parent.config.find('.tableadd'));
    if (new_form_link.length > 0){
        parent.ele.find(".dataTables_filter").append(new_form_link);
        function reload_table(data){
            parent.oTable.fnDraw();
        }
        new_form_link.attr('rel', form_id);
        parent.link_form = new LIMBO.AjaxLinkForm(new_form_link, reload_table);
    }
});

BaseDataTable.method("row_data", function(data, keymap){
    // Keymap is a map of {table_key:data_key}
    var row = [];
    this.config.find('.col_menu_html ul li a').each(function(){
        var key = $(this).attr('title');
        var value = undefined;
        if (key != undefined){
            value = data[key];
        }
        if (keymap != undefined && keymap[key] != undefined && data[keymap[key]] != undefined){
            value = data[keymap[key]];
        }
        if (value == undefined){
            value = '';
        }
        row.push(value);
    });
    return row;
});

BaseDataTable.method("find_row", function(key, data, keymap){
    // Keymap is a map of {table_key:data_key}
    var table_data = this.oTable.fnGetData();
    var data_key = key;
    if (keymap != undefined && keymap[key] != undefined){
        data_key = keymap[key];
    }
    for (var index in table_data){
        if (data[data_key] == table_data[index][this.rcolumns[key]]){
            return index
        }
    }
    return -1;
});

BaseDataTable.method("update_row", function(key, data, keymap, redraw){
    // Keymap is a map of {table_key:data_key}
    var index = this.find_row(key, data, keymap);
    if (redraw == undefined){
        redraw = true;
    }
    this.oTable.fnUpdate(this.row_data(data, keymap), index, redraw);
});

BaseDataTable.method("update_or_create_row", function(key, data, keymap, redraw){
    // Keymap is a map of {table_key:data_key}
    var index = this.find_row(key, data, keymap);
    if (redraw == undefined){
        redraw = true;
    }
    if (index != -1){
        return this.oTable.fnUpdate(this.row_data(data, keymap), index, redraw);
    } else {
        return this.add_row(data, keymap);
    }
});

BaseDataTable.method("add_row", function(data, keymap, redraw){
    // Keymap is a map of {table_key:data_key}
    if (redraw == undefined){
        redraw = true;
    }
    return this.oTable.fnAddData(this.row_data(data, keymap), redraw);

});

BaseDataTable.method("remove_row", function(key, data, keymap, redraw){
    // Keymap is a map of {table_key:data_key}
    if (redraw == undefined){
        redraw = true;
    }
    function cb(row){ console.log('removed row {0}.'.format(row));}
    var index = this.find_row(key, data, keymap)
    if (index >= 0){
        return this.oTable.fnDeleteRow(index, cb, redraw);
    }
});

function StaticDataTable(sel) {
    var parent = this;
    this.setup(sel);
    var table = this.table;
    var $$ = this.$$;
    var ele = this.ele;
    this.init();

}

StaticDataTable.inherits(BaseDataTable);

StaticDataTable.method("get_table_args", function(){
    var tbl_args = this.uber('get_table_args');
    tbl_args.bServerSide = false;
    if (this.aoColumns.length != 0){
        tbl_args["aoColumns"] = this.aoColumns;
    }
    return tbl_args;
});


function ServerDataTable(sel) {
    var parent = this;
    this.setup(sel);
    var source = this.source = this.ele.find('.server_table_config a.tablesource')[0].getAttribute('href');

    this.query_data = function (aoData){
        var data = {};
        var key;
        if (aoData != undefined){
            for (key in aoData){
                var o = aoData[key];
                data[o.name] = o.value;
            }
        }
        for (key in LIMBO.GET){
            data[key] = LIMBO.GET[key];
        }
        var tdata = $.param(data, true);
        tdata += '&' + parent.advanced_search.find('input, select, textarea').serialize();
        return tdata;
    };
    this.init();
}

ServerDataTable.inherits(BaseDataTable);


ServerDataTable.method("get_table_args", function(){
    var parent = this;
    var tbl_args = this.uber('get_table_args');
    tbl_args.bServerSide = true;
    tbl_args.sAjaxSource = this.source;

    tbl_args.fnServerData = function ( sSource, aoData, fnCallback ) {
        var data = parent.query_data(aoData);
        $.ajax({
            url: sSource,
            dataType: 'json',
            data: data,
            success: function(json){
                fnCallback(json)
            }
        });
    };

    if (this.aoColumns.length != 0){
        tbl_args["aoColumns"] = this.aoColumns;
    }
    return tbl_args;

});


ServerDataTable.method("get_source", function(){
    return this.query_data();
});


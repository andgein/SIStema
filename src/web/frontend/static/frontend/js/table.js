$(document).ready(function() {
    $('.sistema-frontend-table').each(function() {
        var $this = $(this);
        var $table = $this.find('table');
        var url = $this.data('url');
        var prefix = $this.data('prefix');
        var localizationUrl = $this.data('localization-url');
        // TODO: advanced pagination handling
        var pagination_str = $this.data('pagination');
        var paging = pagination_str ? true : false;
        var pagination = paging
            ? pagination_str.split(',').map(function(x) { return parseInt(x); })
            : [];
        var tableOptions = {
            // TODO: correct localization
            language: {
                "processing": "Подождите...",
                "search": "Поиск:",
                "lengthMenu": "По _MENU_ строк на странице",
                "info": "Строки _START_-_END_ из _TOTAL_",
                "infoEmpty": "Нет подходящих строк",
                "infoFiltered": "(отфильтровано из _MAX_ строк)",
                "infoPostFix": "",
                "loadingRecords": "Загрузка данных...",
                "zeroRecords": "Записи отсутствуют.",
                "emptyTable": "В таблице отсутствуют данные",
                "paginate": {
                  "first": "<<",
                  "previous": "<",
                  "next": ">",
                  "last": ">>"
                },
                "aria": {
                  "sortAscending": ": активировать для сортировки столбца по возрастанию",
                  "sortDescending": ": активировать для сортировки столбца по убыванию"
                }
            },
            sDom: '<"dt-panelmenu clearfix"lfr>t<"dt-panelfooter clearfix"ip>',
            paging: paging,
            serverSide: true,
            order: [],
            ajax: function(data, callback, settings) {
                console.log(data);
                console.log(settings);

                var args = {
                    start: data.start,
                    length: data.length,
                };

                if (data.search.value) {
                  args.q = data.search.value;
                }

                if (data.order.length > 0) {
                  var order_by = [];
                  for (var i = 0; i < data.order.length; ++i) {
                    var name = data.columns[[data.order[i].column]].name;
                    if (data.order[i].dir === 'desc') {
                      name = '-' + name;
                    }
                    order_by.push(name);
                  }
                  args.sort = order_by.join(',');
                }

                // Add prefix to all the arguments
                if (prefix) {
                    var prefixed_args = {};
                    for (key in args) {
                        prefixed_args[prefix + '_' + key] = args[key];
                    }
                    args = prefixed_args;
                }

                $.getJSON(url, args, function(response_data) {
                    response_data.draw = data.draw;
                    callback(response_data);
                });
            },
            columns: $table.find('thead th').map(function(i, th) {
              var $th = $(th);
              return {
                name: $th.data('name'),
                data: $th.data('name'),
                orderable: $th.data('orderable'),
              };
            }).get(),
        };
        if (paging) {
            tableOptions.lengthMenu = pagination;
        }
        $table.DataTable(tableOptions);
    });
    /*
    $('.table-panel .table-filter').change(function(){
        var $table_panel = $(this).closest('.table-panel');
        var table_name = $table_panel.data('table-name');
        var table_identifiers = $table_panel.data('table-identifiers');
        var filter = $(this).val();

        var url = '/frontend/table/' + table_name + '/data/?filter=' + encodeURIComponent(filter) + '&' + $.param(table_identifiers)
        $.getJSON(url,
            function(data) {
                var rows = data.rows;
                var $table = $table_panel.find('table tbody');
                $table.find('tr:not(:first-child)').remove();
                $.each(rows, function(row_idx, row) {
                    var $tr = $('<tr>');
                    $.each(row, function(column_idx, column) {
                        var $td = $('<td>').html(column);
                        $tr.append($td);
                    });
                    $table.append($tr);
                });
            })
    });
    */
});

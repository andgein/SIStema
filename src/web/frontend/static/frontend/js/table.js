$(document).ready(function() {
    $('.sistema-frontend-table').each(function() {
        var $this = $(this);
        var $table = $this.find('table');
        var url = $this.data('url');
        var prefix = $this.data('prefix');
        var pagination_str = $this.data('pagination');
        var paging = pagination_str ? true : false;
        var pagination = paging
            ? pagination_str.split(',').map(function(x) { return parseInt(x); })
            : [];
        var dom = 'rt';
        if (paging) {
          dom = '<"dt-panelmenu clearfix"lr>t<"dt-panelfooter clearfix"ip>';
        }
        var tableOptions = {
            // TODO: correct localization
            language: {
                "processing": "Подождите...",
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
            dom: dom,
            paging: paging,
            serverSide: true,
            processing: true,
            order: [],  // TODO: order by the first orderable column
            ajax: function(data, callback, settings) {
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

        // Set up global search
        $this.find('.global-search').keyup(function() {
          $table.DataTable().search($(this).val()).draw();
        });
    });
});

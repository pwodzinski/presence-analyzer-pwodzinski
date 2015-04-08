google.load("visualization", "1", {packages:["corechart"], 'language': 'pl'});

(function($) {
    $(document).ready(function() {
        var loading = $('#loading');
        $.getJSON("/api/v2/users", function(result) {
            var dropdown = $("#user_id");
            $.each(result, function(item) {
                dropdown.append($("<option />").val(this.user_id).text(this.name));
            });
            dropdown.show();
            loading.hide();
        });
        $('#user_id').change(function() {
            var selected_user = $("#user_id").val(),
                chart_div = $('#chart_div');
            if(selected_user) {
                loading.show();
                chart_div.hide();
                $.getJSON("/api/v2/users", function(result) {
                    $.each(result, function(item) {
                        if (selected_user == this.user_id) {
                            userPhoto = $("#userPhoto").attr("src", this.avatar)
                        }
                    });
                    userPhoto.show();
                });
                $.getJSON("/api/v1/mean_time_weekday/"+selected_user, function(result) {
                    $.each(result, function(index, value) {
                        value[1] = parseInterval(value[1]);
                    });
                    var data = new google.visualization.DataTable();
                    data.addColumn('string', 'Weekday');
                    data.addColumn('datetime', 'Mean time (h:m:s)');
                    data.addRows(result);
                    var options = {
                        hAxis: {title: 'Weekday'}
                    },
                        formatter = new google.visualization.DateFormat({pattern: 'HH:mm:ss'});
                    formatter.format(data, 1);
                    chart_div.show();
                    loading.hide();
                    var chart = new google.visualization.ColumnChart(chart_div[0]);
                    chart.draw(data, options);
                }).error(function() {
                    loading.hide();
                    chart_div.show();
                    $('#chart_div').text("No information about user in database!");
                });
            }
        });
    });
})(jQuery);

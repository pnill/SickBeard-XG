$(document).ready(function(){
    var loading = '<img src="' + sbRoot + '/images/loading16.gif" height="16" width="16" />';

    function toggle_torrent_title(){
        if ($('#use_torrents').prop('checked')) {
            $('#no-torrents').show();
        } else {
            $('#no-torrents').hide();
        }
    }

    $.fn.nzb_method_handler = function() {

        var selectedProvider = $('#nzb_method :selected').val();

        if (selectedProvider == "blackhole") {
            $('#blackhole_settings').show();
            $('#xg_settings').hide();
            $('#testXG').hide();
            $('#testXG-result').hide();
            $('#nzbget_settings').hide();
        } else if (selectedProvider == "nzbget") {
            $('#blackhole_settings').hide();
            $('#sabnzbd_settings').hide();
            $('#testXG').hide();
            $('#testXG-result').hide();
            $('#nzbget_settings').show();
        } else {
            $('#blackhole_settings').hide();
            $('#xg_settings').show();
            $('#testXG').show();
            $('#testXG-result').show();
            $('#nzbget_settings').hide();
        }

    };

    $('#nzb_method').change($(this).nzb_method_handler);

    $(this).nzb_method_handler();

    $('#testXG').click(function(){
        $('#testXG-result').html(loading);
        var xg_host = $("input=[name='xg_host']").val();
        var xg_apiKey = $("input=[name='xg_apikey']").val();

        $.get(sbRoot + "/home/testXG", {'host': xg_host, 'apikey': xg_apiKey}, 
        function (data){ $('#testXG-result').html(data); });
    });

    $('#use_torrents').click(function(){
        toggle_torrent_title();
    });

    toggle_torrent_title();

});

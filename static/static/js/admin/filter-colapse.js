;(function($){ $(document).ready(function(){
    $('#changelist-filter').children('h3').each(function(){
        var $title = $(this);
        $title.text('+' + $title.text());
    	$title.next().hide();
        $title.click(function(){
            $title.next().slideToggle();
        });
    });   
  });
})(django.jQuery);
/*
 * box widget
 * <box type=[primary, default, import, success, warning]>
 */
riot.tag2('box', '<div class="{box: true,     box-primary: opts.option==\'primary\',     box-success: opts.option==\'success\',     box-warning: opts.option==\'warning\',     box-info: opts.option==\'info\',     box-danger: opts.option==\'danger\',     box-default: opts.option==\'default\' || !opts.option}"> <div class="{box-header:true, with-border:opts.border}" if="{opts.subject}" data-is="box-header"> <yield from="tools"></yield> </div> <div class="box-body"> <yield from="body"></yield> </div> </div>', '', '', function(opts) {
});

riot.tag2('box-header', '<h3 class="box-title">{parent.opts.subject}</h3> <div class="box-tools pull-right" if="{parent.opts.collapse || parent.opts.remove}"> <yield></yield> <button type="button" class="btn btn-box-tool" data-widget="collapse" if="{parent.opts.collapse}"> <i class="fa fa-minus"></i> </button> <button type="button" class="btn btn-box-tool" data-widget="remove" if="{parent.opts.remove}"> <i class="fa fa-times"></i> </button> </div>', '', '', function(opts) {
});

/*
 * callout
 * <callout subject="subect">
 *   <p>This is a test</p>
 * </callout>
 */

riot.tag2('callout', '<div class="callout callout-{opts.option}"> <h4 if="{opts.subject}">{opts.subject}</h4> <yield></yield> </div>', '', '', function(opts) {
});
var morsels = window.morsels || {};

(function () {
	"use strict";
	var init, addUploadUI;

	init = function () {
		addUploadUI();
	};

	addUploadUI = function () {
		var uploadWidget = $('#fileupload');
		uploadWidget.fileupload({
			acceptFileTypes:/(\.|\/)(jpe?g)|png|ogg|gif|tiff|bmp|ico|mp3$/i, //Add supported file types here
			maxNumberOfFiles:10, //Change max number of files
			maxChunkSize:500 * 1024, //500KB each request will send 500KB of data.
			maxRetries:20, //Number of times to retry upload
			retryTimeout:1000,
			sequentialUploads:true,
			autoUpload:false,

			uploadTemplate:function (o) {
				var rows = $();
				_.each(o.files, function (file) {
					var row = _.template($("#template-upload").html(), {file: file, o:o});
					rows = rows.add(row);
				});
				return rows;
			},

			downloadTemplate:function (o) {
				var rows = $();
				_.each(o.files, function (file) {
					var row = _.template($("#template-download").html(), {file: file, o:o});
					rows = rows.add(row);
				});
				return rows;
			},

			add:function (e, data) {
				//Hook for adding a new file to the uploader 
				var self = this;
				var fileName = data.files[0].name;
				$.getJSON(morsels.urls.IMAGE_UPLOAD, {file:fileName }, function (response) {
					data.url = response && response.url;
					data.uploadedBytes = response && response.size;
					$.blueimpUI.fileupload.prototype.options.add.call(self, e, data);
				});

			},

			fail:function (e, data) {
				var self = this;
				var fileName = data.files[0].name;
				var fu = $(self).data('fileupload'),
					retries = data.context.data('retries') || 0,
					retry = function () {
						$.getJSON(morsels.urls.IMAGE_UPLOAD, {file:fileName})
							.done(function (response) {
								data.uploadedBytes = response && response.size;
								data.submit();
							})
							.fail(function () {
								fu._trigger('fail', e, data);
							});
					};
				if (data.errorThrown !== 'abort' &&
					data.errorThrown !== 'uploadedBytes' &&
					retries < fu.options.maxRetries) {
					retries += 1;
					data.context.data('retries', retries);
					window.setTimeout(retry, retries * fu.options.retryTimeout);
					return;
				}
				data.context.removeData('retries');
				$.blueimpUI.fileupload.prototype.options.fail.call(self, e, data);
			}

		});
	};

	// export public functions:
	morsels.fileUpload = {init:init};
}());

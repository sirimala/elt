desturl="";

        $.ajax({
                        url:"/uploadredirect",

                        type:'POST',

                        dataType:"text",

                        success: function(data,status){
                            //alert(data);

                            //console.log(data);

                            desturl=data;

                        }

                    });

var audio = document.querySelector('audio');

var recordVideo = document.getElementById('record-video');

var container = document.getElementById('container');
var isFirefox = true;
var recordAudio, recordVideo;

function PostBlob(blob, fileType, fileName) {
    // FormData
    var formData = new FormData();
    formData.append(fileType + '-filename', fileName);
    formData.append(fileType + '-blob', blob);

	// POST the Blob using XHR2
    xhr(desturl, formData, function(fileURL) {
    container.appendChild(document.createElement('hr'));
    var mediaElement = document.createElement(fileType);
    var source = document.createElement('source');
    var href = location.href.substr(0, location.href.lastIndexOf('/') + 1);
    source.src = href + fileURL;
    if (fileType == 'video') source.type = 'video/webm; codecs="vp8, vorbis"';
    if (fileType == 'audio') source.type = !!navigator.mozGetUserMedia ? 'audio/ogg' : 'audio/wav';

    mediaElement.appendChild(source);
    mediaElement.controls = true;
    mediaElement.play();
    });
}
function interfaceRecord() {
	navigator.getUserMedia({
        audio: true,
        video: false
    }, function(stream) {
    recordAudio = RecordRTC(stream, {
    onAudioProcessStarted: function() {
        if (!isFirefox) {
            recordVideo.startRecording();
        }
    }
    });
    if (isFirefox) {
        $("#record").html("Recording...");
        recordAudio.startRecording();
    }
    if (!isFirefox) {
        recordVideo = RecordRTC(stream, {
            type: 'video'
        });
        recordAudio.startRecording();
    }
    }, function(error) {
    alert(JSON.stringify(error, null, '\t'));
    });
}
function interfaceStop() {
	fileName = Math.round(Math.random() * 99999999) + 99999999;

    if (!isFirefox) {
        recordAudio.stopRecording(function() {
            PostBlob(recordAudio.getBlob(), 'audio', fileName + '.wav');
        });
    } else {
        recordAudio.stopRecording(function(url) {
            PostBlob(recordAudio.getBlob(), 'video', fileName + '.webm');
        });
    }
    if (!isFirefox) {
        recordVideo.stopRecording(function() {
            PostBlob(recordVideo.getBlob(), 'video', fileName + '.webm');
        });
    }
}
function deleteAudioVideoFiles() {
    deleteFiles.disabled = true;
    if (!fileName) return;
    var formData = new FormData();
    formData.append('delete-file', fileName);
    xhr('delete.php', formData,function(response) {
    console.log(response);
    });
    fileName = null;
    container.innerHTML = '';
}
function xhr(url, data, callback) {
    var request = new XMLHttpRequest();
    request.onreadystatechange = function() {
        if (request.readyState == 4 && request.status == 200) {
            callback(request.responseText);
        }
    };
    request.open('POST', url);
    request.send(data);
}

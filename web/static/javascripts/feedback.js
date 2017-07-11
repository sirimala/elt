var feedbackView={

			init: function(){
				this.titlePane = $(".title");
				this.sectionName = $("#section-name");
				this.questionPane = $("#content-box");
				this.questionNote = $("#question-instructions");
				this.backdiv = $("#back");
				this.progressbox = $("#progress-box");
				this.examplePane = $("#examplecontent");
				// create back button
				var btn = document.createElement("BUTTON");
				var t = document.createTextNode("Back");
				btn.appendChild(t);
				btn.setAttribute("id", "backbtn");
				this.backdiv.replaceWith(btn);
				this.backbtn = $("#backbtn");
				this.backbtn.addClass("btn btn-primary");
				this.backbtn.click(function(){	
					resultView.render();
					$('#backbtn').hide();
					$('#progress-box').html("");
					$("#examplecontent").html('');
				});
			},
			getQid : function(qid){
				$.each(quizModel.questions, function(index, value) {
					if (value.id == qid){
						console.log(value);
						feedbackView.render(value);
						return;	
					}
					
				});
			},
			render : function(data){
				$('#backbtn').show();
				$('#progress-box').show();
				this.displayAnswer(data);
				var q = data;
				this.sectionName.html("<h4>");
				this.sectionName.append(q.section + "&nbsp; - &nbsp;");
				this.sectionName.append(q.subsections.name);
				this.sectionName.append("</h4>");
				this.questionNote.html("");
				this.questionPane.html('<br><p class="lead">' + q.question + '</p>');

				if (q.subsections.types == "passage"){
					feedbackView.displayPassage(data);
					feedbackView.displayOptions(data);
				}

				if (q.subsections.types == "essay")
				{
					feedbackView.displayEssay(data);
				}
				if (q.subsections.types == "video"){
					feedbackView.displayVideo(data);
					feedbackView.displayOptions(data);
				}
				if (q.subsections.types == "record")
				{
					//startView.wami1.show();
					questionView.displayRecording();
				}
					
				if (q.subsections.types == "question")
				{
					feedbackView.displayOptions(data);
				}
			},
			displayAnswer : function(data){
				var q=data;
				if (q.answer == ""){
					this.progressbox.hide();
				}
				this.progressbox.append('<br><br><br><h4><b>Feedback:</b></h4><div style="display: flex">');
				if (q.subsections.types == "video"){
					this.progressbox.append('<br>Please watch the video between the time stamps specified to identify the correct answer for the given question.<br><b>Time stamp:</b>' + q.answer + '<br>');
				}
				else if(q.subsections.types == "passage"){
					if(q.subsections.name=="A2-Reading"){
						this.progressbox.append('<br>' + q.answer + '<br>');
					}
					else{
						this.progressbox.append('<br><div><image src="img/arrow_r.png" width="55" height="25"> The highlighted text in the passage is the pointer to the correct option.<br><br><b>Following is the text from the passage that indicates the answer for the given question:</b><br><image src="img/bullet_h.png" width="25",height="10">' + q.answer + '<br></div>');
					}
				}
				else{
					this.progressbox.append('<br>' + q.answer + '<br>');
				}
				if(q.subsections.types != "passage" && q.subsections.types !="video"){
					this.progressbox.append("<h4>Examples:</h4>Click this button to ");
					var btn = document.createElement("BUTTON");
					btn.appendChild(document.createTextNode("View Examples"));
					btn.setAttribute("ID","ex");
					btn.setAttribute("class", "btn btn-primary btn-xs");
					btn.setAttribute("data-toggle","modal");
					btn.setAttribute("data-target", "#myModal");
					this.progressbox.append(btn);
					this.examplePane.append(q.examples);
					$("#ex").click(function(){
		
					});
				}
				
				if (q.subsections.name=="T1-Reading"||q.subsections.name=="T2-Listening"||q.practicelinks.length==0){

				}else{
				this.progressbox.append('<br><h4>Practice Links: </h4>');
					for (var i=0;i<q.practicelinks.length;i++){
						this.progressbox.append('<a href="'+q.practicelinks[i]+'" target="_blank">'+q.practicelinks[i]+'</a><br>');
					}
				}
				this.progressbox.append('<br></div>');
			},
			displayOptions : function(data) {
				var q =data;
				var optionsHTML = '';
				for (var i = 0; i < q.options.length; i++) {
					var optionText = q.options[i].substring(1, q.options[i].length);
					optionsHTML += '<div class="radio">';
					optionsHTML += '<label><input type="radio" name="optionsRadios" id="optionsRadios1" value="' + optionText + '"';
					if(q.status && q.responseAnswer == optionText)
						optionsHTML += 'checked';
					if (q.options[i].substring(0,1)=="="){
						optionsHTML += ' disabled><mark style="background-color: #99FF99;color: black;">' + optionText + '</mark></label>';
					}
					else{
						optionsHTML += ' disabled>' + optionText + '</label>';
					}
					optionsHTML += '</div>';
				}
				optionsHTML += '<div class="radio">';
				optionsHTML += '<label><input type="radio" name="optionsRadios" id="optionsRadios1" value="skip" disabled>Skip Question</label>';
				optionsHTML += '</div>';
				this.questionPane.append(optionsHTML);
			},
		displayPassage : function(data) {
			var q = data;
			var anstext = q.answer.trim();
			var psg = q.subsections.passage;
			var startpos = psg.search(anstext);
			if(startpos == -1){
				this.questionNote.append('<div>' + q.subsections.passage + '</div>');
			}else{
				var anslength = anstext.length;
				var endpos = startpos+anslength;
				this.questionNote.append('<div>' + q.subsections.passage.substring(0,startpos));
				this.questionNote.append('<mark style="background-color: yellow;color: black;">' + q.subsections.passage.substring(startpos,endpos) + '</mark>');
				this.questionNote.append(q.subsections.passage.substring(endpos,q.subsections.passage.length)+'</div>');
			}
		},
		displayEssay : function(data) {
			var q = data;
			//this.questionNote.html("");
			var essayText = "";
			if(data.responseAnswer)
				essayText = data.responseAnswer;

			// create text area
			var words = document.createElement("div");
			words.setAttribute("id", "words");
			this.questionPane.append(words);

			this.questionPane.append('<div><textarea style="width: 500px; height: 200px">' +
			essayText + '</textarea>');
			$('textarea').keyup(function () {
				var value = $(this).val();
				var regex = /\s+/gi;
				var wordCount = value.trim().replace(regex, ' ').split(' ').length;
				//console.log("word count" + wordCount);
				$("#words").html("Word Count: " + wordCount);
			});
		},

		displayVideo : function(data) {
			var q = data;
			this.questionNote.append(q.subsections.link);
		}

	};
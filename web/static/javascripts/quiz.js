var quizModel = {

		// instance variables: title, questions
		init : function(data) {
			// create questions array from the JSON data
			this.createQuizModel(data);
			console.log(data)
		},

		// parse JSON data and create an array of questions
		createQuizModel : function(data) {
			// get questions from the json and assign it to questions array
			// add section and subsection to the question object
			var questionsArray = [];
			$.each(data, function (key, value) {

				/*
				 * store quiz title in
				 */
				if (key == "name")
					quizModel.title = value;
				/*
				 * title and test
				 */
				if (key == "quizStatus")
					quizModel.quizStatus = value;

				if (key == "section") {
					$.each(value, function(index, value) {
						var sections = value;
						$.each(sections, function(key, value) {
							if (key == "subsection") {
								$.each(value, function(index, value) {
									var subsections = value;
									$.each(subsections, function(key, value) {
										if (key == "questions") {
											function compare(a,b) {
												if (a.serialno < b.serialno)
													return -1;
												if (a.serialno > b.serialno)
													return 1;
												return 0;
											}
											value.sort(compare);
											$.each(value, function(index, value){
												value.section = sections.name;
												value.subsections = subsections;
												value.options = Randomiser.shuffle(value.options);
												questionsArray.push(value);
											});
										}
									});
								});
							}
						});
					});
				}
			});
			this.questions = questionsArray;

			/*
			 *	Set the question index to the first question that is not attempted
			 */
			var q = 0, qStatus;
			$.each(this.questions, function(index, value) {
				if(!value.status)
					return false;
				q = index;
			});
			this.questionIndex = q;
			//console.log("question index is:" + this.questionIndex)
		},
		getQuizStatus : function() {
			// get the status of the quiz by looking into the questions array
			// returns START, INPROGRESS, END
			return this.quizStatus;
		},
		setQuizStatus : function(quizStatus) {
			this.quizStatus = quizStatus;
		},
		nextQuestion : function() {
			// returns the next questions and updates the pointer
			var quizStatus = this.getQuizStatus();
			//console.log(quizStatus);
			if (quizStatus == "START")
				this.questionIndex = -1;
			if (quizStatus == "END"){
				this.questionIndex = this.questions.length;
				this.question = undefined;
			}
			if (this.questionIndex < this.questions.length) {
				this.questionIndex++;
				if(this.questionIndex == this.questions.length)
					this.questionIndex = this.questions.length - 1;
				this.question = this.questions[this.questionIndex];
			}
		},

		setQuestion : function(index) {
			//$.each(this.questions, function(i, q){
			//	if (i < index)
			//		q.status = "skip";
			//});
			this.questionIndex=index;
			this.question = this.questions[index];
		}
};

var octopus = {
		init : function() {
			$.post("/getquizstatus")
				.done(function(data){
					//console.log("info: questions loaded from server" + data);
					data = JSON.parse(data);
					quizModel.init(data)
					startView.init();
					var status = quizModel.getQuizStatus();
					console.log("quiz status" + status);
					if (status == "END")
						resultView.init();
					else
						startView.render();
				})
				.fail(function(data){
					startView.init();
					startView.showError();
				});
		},
		startTest : function() {
			octopus.pingServer();
			this.pingThread = window.setInterval(function(){
				octopus.pingServer();
			}, 60000);
		},

		stopPing : function() {
			clearInterval(this.pingThread);
		},
		submitAnswer : function() {
			var submittedQuestion = $.extend({},quizModel.question);

			if(quizModel.question.subsections.types == 'essay')
				questionView.stopautosave();

			submittedQuestion.subsections = undefined;
			data = JSON.stringify({jsonData: submittedQuestion});
			$.post("/submitanswer", data)
				.done(function(data){
					//console.log("Success:" + data);
					data = JSON.parse(data)
					if(data.testEnd) {
						quizModel.testEnd = true;
					}
					if(quizModel.getQuizStatus() == "END")
						resultView.init();
					if(quizModel.getQuizStatus() == "INPROGRESS") {
						if(quizModel.questionIndex == quizModel.questions.length - 1)
							alert("Click on End Test button to finish.");
						questionView.showNextQuestion();
					}
				});
		},
		autosaveContent : function(responseAnswer, responseTS) {
			// grab the current question object from model
			var q = quizModel.question;

			// update the question object
			// with response answer and response time
			q.responseAnswer = responseAnswer;
			q.responseTime = responseTS;
			//console.log(q);
			// call server side submit function
			// creating json file for submit response
			var data = {"currentQuestion": q.id, "draft":responseAnswer,"responsetime":q.responseTime}
			data=JSON.stringify({jsonData: data});
			$.post("/autosaveEssay", data)
				.done(function(data){
					//console.log("Success:" + data);
				});
		},
		getResults : function() {
			$.ajax({
				type: 'get',
				url: '/getResult',
				dataType:'json',
				async: false,
				success: function (data) {
					data = JSON.stringify(data);
					quizModel.result = JSON.parse(data);
				},
				error: function () {
					alert("failure");
				}
			});
		},
		pingServer : function() {
			$.post("/testtime")

				.done(function(data){
					//console.log("ping response " + data)
					data = JSON.parse(data);
					quizModel.setQuizStatus(data.quizStatus);
					if(!data.timeRemaining) {
						this.pingThread = clearInterval();
					}
					progressView.renderTime(data.timeRemaining);
				})
				.fail(function(){
					//console.log("PING Failed");
				});
		},
		endTest : function() {
			progressView.progressBox.html("");
			progressView.timeBox.html("");
			resultView.init();
			//console.log("score="+resultView.totalScore);
			var data = {"testend":true, "finalScore": resultView.finalScore,"spklink": resultView.spklink};

			data=JSON.stringify({jsonData: data});
			//console.log("endtest" + data);
			$.post("/endtest", data)
				.done(function(data){
					//console.log("Success:" + data);
				})
				.fail(function(data){
					//console.log("testend Failed");
				});
			octopus.stopPing();
		}
};

var startView = {
		init : function() {
			this.titlePane = $(".title");
			this.sectionName = $("#section-name");
			this.questionPane = $("#content-box");
			this.QuestionV=$('#QuestionView');

			this.startMessage = "Click the Start Test button to begin.";
			this.resumeMessage = "You have started the test, click the button below to resume the test.";
			this.resumeMessage += " Click the Resume Test button to resume.";
			this.errorMessage = "There is a problem with starting your test session. Refresh the page. ";
			this.errorMessage += "If the problem persists then report Error 100 to your test administrator.";

			this.navBar = $("#nav-bar");
			//add this button in JS
			//<button id="start-btn" class="btn btn-lg btn-success">Start Test</button>
			// create start/resume button
			var btn = document.createElement("BUTTON");
			var t = document.createTextNode("Start Test");
			btn.appendChild(t);
			btn.setAttribute("id", "start-btn");
			this.navBar.append(btn);

			this.startButton = $("#start-btn");
			this.startButton.addClass("btn btn-primary btn-lg")
			
			var w=document.createElement("div");
			w.setAttribute('id','flash');
			this.QuestionV.append(w);
			this.wami1 = $("#flash");
			this.wami1.hide();

			this.startButton.click(function(){
				startView.startButton.hide();
				if(quizModel.testEnd)
					resultView.init();
				else {
					octopus.startTest();
					quizModel.nextQuestion();
					questionView.init();
					questionView.render();
					progressView.init();
				}
			});

			this.endtestdiv = $('#end-test');
			var btn = document.createElement("BUTTON");
			var t = document.createTextNode("End Test");
			btn.appendChild(t);
			btn.setAttribute("id", "endbtn");
			this.endtestdiv.append(btn);
			this.endtest = $("#endbtn");
			this.endtest.addClass("btn btn-danger");
			this.endtest.hide();

			this.endtest.click(function(){
				if(confirm("Do you want to end the test?") == true) {
					octopus.endTest();
				}
			});
		},

		render : function() {
			this.titlePane.html(quizModel.title);
			var quizStatus = quizModel.getQuizStatus();
			if(quizStatus == "START") {
				this.questionPane.html('<h3>' + this.startMessage + '</h3><br>');
			} else if (quizStatus == "INPROGRESS") {
				this.questionPane.html(this.resumeMessage);
				this.startButton.html("Resume Test");
				this.startButton.addClass("btn btn-info");
			}
			this.startButton.show();
		},

		showError : function() {
			this.questionPane.html('<p class="lead">' + this.errorMessage + '</p>');
			this.startButton.hide();
		}
};

var questionView = {
		init : function() {
			// get references to all html elements
			this.titlePane = $(".title");
			this.sectionName = $("#section-name");
			this.questionPane = $("#content-box");
			this.questionNote = $("#question-instructions");

			this.navBar = $("#nav-bar");

			// create answer button
			var btn = document.createElement("BUTTON");
			var t = document.createTextNode("Submit Answer");
			btn.appendChild(t);
			btn.setAttribute("id", "sanswer");
			this.navBar.append(btn);
			this.answerButton = $("#sanswer");
			this.answerButton.addClass("btn btn-success");

			startView.endtest.show();

			this.answerButton.click(function(){

				var q = quizModel.question;
				var selectedAnswer = $("input:checked").val();
				var audiolink = $("#audiolink").val();
				if (q.subsections.types == "essay") {
					selectedAnswer = $("textarea").val();
					if (!selectedAnswer)
						selectedAnswer = "skip";
				}

				if (q.subsections.types == "record") {
					selectedAnswer = audiolink;
					if (!selectedAnswer)
						selectedAnswer = "skip";

					//Wami.stopRecording();
				}

				if (selectedAnswer == "skip") {
					q.status = "skip";
					q.responseAnswer = "skip";
					questionView.submittedTS = Date.now();
					q.responseTime = questionView.getResponseTime();
					octopus.submitAnswer();
				} else if (selectedAnswer){
					q.status = "submitted";
					q.responseAnswer = selectedAnswer;
					questionView.submittedTS = Date.now();
					q.responseTime = questionView.getResponseTime();
					octopus.submitAnswer();
				} else {
					alert("Select a choice to submit answer.");
				}
			});
		},

		showQuestion : function(){
			if(quizModel.question){
				questionView.render();
				progressView.init();
			}
		},

		showNextQuestion: function() {
			quizModel.nextQuestion();
			this.showQuestion();
		},

		render : function() {
			var q = quizModel.question;
			this.sectionName.html("<h4>");
			this.sectionName.append(q.section);
			// this.sectionName.append(q.subsections.name);
			this.sectionName.append("</h4>");
			this.questionNote.html('<p class="lead">' + q.subsections.note + '</p>');
			this.questionPane.html('<p class="lead">' + q.question + '</p>');

			if (q.subsections.types == "passage"){
				this.displayPassage();
				this.displayOptions();
			}

			if (q.subsections.types == "essay")
			{
				this.displayEssay();
				this.myvar = setInterval(function() {
					var text = $('textarea').val();
					octopus.autosaveContent(text,Date.now()/(1000*60));
				},30000);

			}
			if (q.subsections.types == "video"){
				this.displayVideo();
				this.displayOptions();
			}
			if (q.subsections.types == "record")
			{
				this.questionPane.append('<div><label>Please Watch the instructions:</label><br><iframe width=\"560\" height=\"315\" src=\"static/Intro-SpeakingSection.mp4\" frameborder=\"0\" allowfullscreen></iframe></div><br>');
				this.questionPane.append('<div><label>Please Click on URL Link: &nbsp;</label><a href="http://vocaroo.com/" target="_blank">http://vocaroo.com/</a></div><br>');
				this.questionPane.append('<div><label>Audio Link: </label><input type="text" id="audiolink"></div>');
				this.questionPane.append('<br><label><input type="radio" name="optionsRadios" id="optionsRadios1" value="skip"> Skip Question</label>');
				//startView.wami1.show();
				//this.displayRecording();
			}
				
			if (q.subsections.types == "question")
				this.displayOptions();
			this.appearedTS = Date.now();
			this.answerButton.show();
		},

		stopautosave : function() {
			clearInterval(this.myvar);
		},

		displayPassage : function() {
			var q = quizModel.question;
			this.questionNote.append('<div>' + q.subsections.passage +'</div>');
		},

		displayEssay : function() {
			var q = quizModel.question;
			this.questionNote.html("");
			var essayText = "";
			if(quizModel.question.responseAnswer)
				essayText = quizModel.question.responseAnswer;

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

		displayVideo : function() {
			var q = quizModel.question;
			this.questionNote.append(q.subsections.link);
		},

		displayRecording : function() {
			Wami.setup({
					id: 'flash'
				});
			var q = quizModel.question;
			var instructions = "<ol><li><b>Select allow recording in flash player settings</b></li><li>Click on close button</li>" +
				"<li>Click on record button</li><li>Speak into the microphone</li><li>Click on Stop</li><li>Submit your answer.</li></ol>";
			this.questionPane.append(instructions);
			this.questionPane.append('<div><button id="record" class="btn btn-danger">Record</button>'+
			'&nbsp;&nbsp<button id="stop" class="btn btn-info">Stop</button></div>');
			var record=document.getElementById('record');
			var stop=document.getElementById('stop');
			stop.disabled=true;
			record.onclick= function()
			{
				record.disabled=true;
				stop.disabled=false;
				var recordingUrl ="https://wise-logic-91506.appspot.com/audio";
				Wami.startRecording(recordingUrl);
			}
			stop.onclick= function()
			{
				Wami.stopListening();
				record.disabled=false;
				stop.disabled=true;
			}
		},

		displayOptions : function() {
			var q = quizModel.question;
			var optionsHTML = '';
			for (var i = 0; i < q.options.length; i++) {
				var optionText = q.options[i].substring(1, q.options[i].length);
				optionsHTML += '<div class="radio">';
				optionsHTML += '<label><input type="radio" name="optionsRadios" id="optionsRadios1" value="' + optionText + '"';
				if(q.status && q.responseAnswer == optionText)
					optionsHTML += 'checked';
				optionsHTML += '>' + optionText + '</label>';
				optionsHTML += '</div>';
			}
			optionsHTML += '<div class="radio">';
			optionsHTML += '<label><input type="radio" name="optionsRadios" id="optionsRadios1" value="skip">Skip Question</label>';
			optionsHTML += '</div>';
			this.questionPane.append(optionsHTML);
		},

		getResponseTime : function() {
			return (questionView.submittedTS - questionView.appearedTS)/(1000);
		},

		reset : function() {
			this.questionPane.hide();
			this.navBar.hide();
		}
};

var progressView = {

		init : function() {
			// get references to all html elements
			this.progressBox = $("#progress-box");
			this.progressBox.html("");
			this.timeBox = $("#time-box");
			this.render();
		},

		render : function() {
			progressView.progressBox.append('<h3>Test Progress</h3><div style="display: flex">');
			var section, buttonCount = 0;
			$.each(quizModel.questions, function(index, question){

				if(section != question.section){
					buttonCount = 0;
					if(section){
						progressView.progressBox.append("</div></div>");
					}
					section = question.section;
					var sectionLabel = '<div style="display: flex"><div><b>' +
						section + '</b></div><div>';
					progressView.progressBox.append(sectionLabel);
				}
				if(index < 8)
					buttonLabel = ' ' + (index + 1);
				else
					buttonLabel = index + 1;

				if(!question.status)
					buttonColor = "btn-default";
				if(question.status == "skip")
					buttonColor = "btn-warning";
				if(question.status == "submitted")
					buttonColor = "btn-success";
				if(question == quizModel.question)
					buttonColor = "btn-primary";

				var btn = document.createElement("BUTTON");
				var t = document.createTextNode(buttonLabel + ' ');
				btn.appendChild(t);
				btn.setAttribute("id", index);

				//qButtonHTML = '<button class="btn btn-xs ' + buttonColor + '" id="qbutton' + index + '">' + buttonLabel + '</button>&nbsp;';
				buttonCount++;

				progressView.progressBox.append(btn);
				$("#"+index).addClass("btn btn-xs " + buttonColor);
				if(!question.status)
					$("#"+index).attr('disabled','disabled');
				$("#"+index).click(function(){
					//console.log("progress:" + this.id);
					quizModel.setQuestion(this.id);
					questionView.showQuestion();
				});
			});
		},

		reset : function() {
			this.progressBox.html("");
		},

		renderTime : function(remainingTime) {
			if(!remainingTime)
				remainingTime = 0;
			buttonColor = "btn-primary";
			remainingTime = Math.round(remainingTime/60);
			buttonText = remainingTime + " minutes remaining";
			if(remainingTime <= 5) {
				buttonColor = "btn-warning";
			}
			if(remainingTime == 1) {
				buttonColor = "btn-danger";
				buttonText = "One minute left..."
			}
			if(remainingTime <= 0) {
				buttonColor = "btn-danger";
				buttonText = "Time is up!"
				octopus.endTest();
				//window.setInterval(function(){
				//	location.reload();
				//},3000);
				//resultView.init();
			}
			this.timeBox.html('<button type="button" class="btn btn-lg btn-block '+ buttonColor +'">'+
			buttonText +'</button>');

		}
};

var resultView = {
		init : function() {
			// get references to all html elements
			this.titlePane = $(".title");
			this.sectionName = $("#section-name");
			this.questionPane = $("#content-box");
			this.questionNote = $("#question-instructions");

			this.navBar = $("#nav-bar");
			this.startButton = $("#start-btn");
			this.answerButton = $("#answer");

			this.startButton.hide();
			this.answerButton.hide();
			startView.endtest.hide();

			this.render();

		},

		render : function() {
			//progressView.init();
			//progressView.reset();
			this.sectionName.html("You have completed the test.");
			octopus.getResults();
			this.questionPane.html("");
			totalScore = 0;
			spklink ="";
			count=0;
			var table = document.createElement("TABLE");
			this.questionPane.append(table);
			var tr = document.createElement("TR");
			var td = document.createElement("TH");
			var t = document.createTextNode("Section");
			td.appendChild(t);
			var td1 = document.createElement("TH");
			var t1 = document.createTextNode("Score ");
			td1.appendChild(t1);
			var td2 = document.createElement("TH");
			var t2 = document.createTextNode("Submitted Answer");
			td2.appendChild(t2);
			var td3 = document.createElement("TH");
			var t3 = document.createTextNode("View Answer");
			td3.appendChild(t3);
			tr.appendChild(td);
			tr.appendChild(td1);
			tr.appendChild(td2);
			tr.appendChild(td3);
			table.appendChild(tr);
			var tr3 = document.createElement("TR");
			var tde3 = document.createElement("TD");
			tde3.setAttribute("colspan","4");
			var line = document.createElement("HR");
			tde3.appendChild(line);
			tr3.appendChild(tde3);
			table.appendChild(tr3);
			$.each(quizModel.result.question,function(index, value){
				var tr1 = document.createElement("TR");
				var td4 = document.createElement("TD");
				var section="";
				$.each(quizModel.questions, function(index, value1) {
					if (value.currentQuestion == value1.id){
						section = value1.subsections.name;
						return;
					}
				});
				var t4 = document.createTextNode(section);
				td4.appendChild(t4);
				if(section=="E3-Speaking"){
					spklink=value.submittedans;
				}
				var td5 = document.createElement("TD");
				var t5 = document.createTextNode(value.q_score);
				td5.appendChild(t5);
				var td6 = document.createElement("TD");
				var t6 = document.createTextNode(value.submittedans);
				td6.appendChild(t6);
				var td7 = document.createElement("TD");
				var btn = document.createElement("BUTTON");
				btn.appendChild(document.createTextNode("ViewAnswer"));
				btn.setAttribute("ID",value.currentQuestion);
				btn.setAttribute("class", "btn btn-primary btn-xs");
				if(section == "A5-Composition" || section == "E4-Writing" || section == "E3-Speaking"){
				}else{
					td7.appendChild(btn);
				}
				tr1.appendChild(td4);
				tr1.appendChild(td5);
				tr1.appendChild(td6);
				tr1.appendChild(td7);
				//create hr element in tr
				table.appendChild(tr1);
				var tr2 = document.createElement("TR");
				var tde = document.createElement("TD");
				tde.setAttribute("colspan","4");
				var line1 = document.createElement("HR");
				tde.appendChild(line1);
				tr2.appendChild(tde);
				table.appendChild(tr2);
				$("#"+value.currentQuestion).click(function(){
                  //alert(value.currentQuestion);
                  feedbackView.init();
                  feedbackView.getQid(value.currentQuestion);
              	});
				totalScore += value.q_score;
				count +=1;
			});
			
			this.questionNote.html('<p class="lead">Your total score is: ' + totalScore + '</p>');
			//this.questionPane.hide();
			this.navBar.hide();
			this.finalScore = totalScore;
			this.spklink = spklink;
			console.log(this.finalScore);
		},	
};

// used for shuffling the options in MCQs
var Randomiser = {
		shuffle : function (array) {
			var currentIndex = array.length, temporaryValue, randomIndex ;

			// While there remain elements to shuffle...
			while (0 !== currentIndex) {

				// Pick a remaining element...
				randomIndex = Math.floor(Math.random() * currentIndex);
				currentIndex -= 1;

				// And swap it with the current element.
				temporaryValue = array[currentIndex];
				array[currentIndex] = array[randomIndex];
				array[randomIndex] = temporaryValue;
			}

			return array;
		}
};



var down  = 0x01;
var right = 0x02;
var up    = 0x04;
var left  = 0x08;

function keycodeMask(keycode) {
    if (37 <= keycode && keycode <= 40) {
        return 1 << (40 - keycode);
    } else {
        return 0;
    }
}

var runningTimer = false;
var killTimer = false;
function setInterval(time, first_run) {
    if (!first_run && killTimer) {
        killTimer = false;
        return;
    }
    runningTimer = true;
    var minutes = Math.round(time/1000 / 60000);
    var seconds = Math.round(time/1000 % 60);

    $('#timer').html('[' + minutes + ':' + seconds + ']');
    if (time > 0) {
        setTimeout(function() { setInterval(time - 1000); }, 1000);
    } else {
        runningTimer = false;
    }

}

function setStatus(msg) {
    $('#status').html(msg);
}


var state = {
    participating: false,
    controlling: false,
    pressed_state: 0,
    sensors_form: $('<form></form>'),
    sensors: {},

    press: function(keycode) {
               this.setPressedState(this.pressed_state | keycodeMask(keycode));
           },
    unpress: function(keycode) {
                 this.setPressedState(this.pressed_state & ~(keycodeMask(keycode)));
             },

    setControlling: function(new_value) {
        this.controlling = new_value;
        this.setDisplay(0);
        if (this.controlling) {
            state.startControl();
        } else {
            state.stopControl();
        }
    },

    setDisplay: function(pressed_state) {
                    var ul = up | left;
                    var ur = up | right;
                    var dl = down | left;
                    var dr = down | right;

                    results = [];
                    results[0] = '∅';
                    results[left] = '←';
                    results[right] = '→';
                    results[down] = '↓';
                    results[up] = '↑';
                    results[ul] = '↖';
                    results[ur] = '↗';
                    results[dl] = '↙';
                    results[dr] = '↘';
                    var res = results[pressed_state];
                    if (!res) {
                        res = results[0];
                    }
                    $('#wheel').html(res);
                },

    setPressedState: function(new_state, force) {
                         if ((this.controlling || force) && 
                                (new_state != this.pressed_state)) {
                             if(this.do_action(new_state)) {
                                 this.pressed_state = new_state;
                             }
                         }
                     },

    do_action: function(pressed_keys) {
                   this.setDisplay(pressed_keys);

                   if ((pressed_keys == (down | up)) ||
                           (pressed_keys == (left | right))) {
                       return false;
                   }


                   var data = $.param({ action: 'control', value: pressed_keys });
                   state.socket.send(data);
                   return true;
               },

    updateSensors: function(new_values) {
                        for (var prop in new_values) {
                            if (new_values.hasOwnProperty(prop)) {
                                var prop_selector = 'input[name="' + prop + '"]';
                                var input = $(prop_selector, this.sensors_form);
                                if (!input.length) {
                                    input = $('<input type="hidden" />');
                                    input.attr("name", prop);
                                    this.sensors_form.append(input);
                                }
                                input.val(new_values[prop]).change();
                                this.sensors[prop] = input;
                            }
                        }
                    },
    setSensors: function(sensors_list) {
                    var sensors = {};
                    $(sensors_list).each(function(idx) {
                        sensors[this] = undefined;
                    });
                    this.updateSensors(sensors);
                },
    startControl: function() {
                      state.setPressedState(0);
                      setStatus('You are driver!');

                      $(document).keydown(function(e) {
                          if (keycodeMask(e.keyCode)) {
                              state.press(e.keyCode);
                              return false;
                          }
                          return true;
                      });

                      $(document).keyup(function(e) {
                          if (keycodeMask(e.keyCode)) {
                              state.unpress(e.keyCode);
                              return false;
                          }
                          return true;
                      });
                  },

    stopControl: function() {
                     state.pressed = 0;
                     setStatus('You are not a driver now.');
                     $(document).unbind('keydown').unbind('keyup');
                 }
};


function updateChargeDisplay(charge, capacity) {
    var ratio = 0;
    if (parseFloat(charge) !== 0) {
        ratio = charge / capacity;
    } 
    var percent = ratio * 100;
    percent = Math.round(percent);

    var width = "250";
    var height = "100";
    var params = $.param({
        chxt: 'y',
        chs: width + "x" + height,
        cht: 'gm', 
        chd: 't:' + percent,
        chtt: 'Battery charge ' + percent + '% (' + charge + '/' + capacity + ' mAh)'
    });

    var new_src = "http://chart.apis.google.com/chart?" + params;
    $('#charge_img').attr('src', new_src);
}


function initBatteryChargeDisplay() {
    var s = state.sensors;
    s.charge.change(function() {
        var new_val = this.value;
        var capacity = s.capacity.val();
        if (!capacity) {
            new_val = 0;
            capacity = 1;
        }
        updateChargeDisplay(new_val, capacity);
    }).change();
}
    
function initBumpersDispaly() {
    var s = state.sensors;
    $(['bump-left', 'bump-right']).each(function(idx) {
        var name = this;
        s[this].change(function() {
            var new_val = this.value;
            var bumper = $('#' + name);
            if (new_val == 'true') {
                bumper.addClass("active");
            } else {
                bumper.removeClass("active");
            }
        }).change();
    });
}

var participation = null;

function initParticipation() {
    participation = {
        name_input: $("#name"),
        part_btn: $('#part'),

        join: function() {
            if (!this.rename()) {
                return false;
            }
            state.participating = true;

            this.part_btn.click(this.part).removeAttr("disabled");

            return false;
        },

        rename: function(new_name) {
                    if (!new_name) {
                        new_name = this.name_input.val();
                    }
                    if (!new_name) {
                        setStatus('<span class="error">Name is required</span>');
                        return false;
                    }

                    var data = $.param({ action: 'name', value: new_name });

                    state.name = new_name;
                    state.socket.send(data);
                    return true;
                },

        part: function() {
                  participation.part_btn.attr("disabled", "disabled");
                  var ws = state.socket;
                  if (ws.readyState == WebSocket.OPEN && state.participating) {
                      state.participating = false;
                      var data = $.param({ action: 'part' });
                      ws.send(data);
                  }
              }
    };
}


function initWs() {
    var ws = new WebSocket('ws://' + location.hostname + ':' + location.port + location.pathname + 'ws');
    state.socket = ws;
    ws.onmessage = function(resp) {
        data = $.parseJSON(resp.data);
        var event = data.event;
        var values = data.values;
        var value = values[0];
        if (data.msg) {
            setStatus(data.msg);
        }
        switch (event) {
            case "user added":
                var new_el = "<li id='user_" + value.id + "'>" + value.name + "</li>";
                $('#participants ul').append(new_el);
                break;
            case "user removed":
                $('#participants ul li#user_' + value.id).remove();
                break;
            case "user renamed":
                value = value[0];
                $('#participants ul li#user_' + value.id).html(value.name);
                break;
            case "new_current":
                $('#participants ul li.current').removeClass('current');
                $('#participants ul li#user_' + value).addClass('current');
                state.setControlling(values[0] == state.id);
                if (runningTimer) {
                    killTimer = true;
                }
                setInterval(values[1]*1000, true);
                break;
            case "your_id":
                state.id = values[0];
                break;
            case "new_img":
                $('#camera img').attr('src', value);
                break;
            case "new_pressed_state":
                state.setDisplay(values[0]);
                break;
            case "sensors-data":
                state.updateSensors(value);
                break;
            case "sensors-list":
                state.setSensors(values);
                initBatteryChargeDisplay();
                initBumpersDispaly();
                break;
        }
    };
}


$(function() {
    initWs();
    initParticipation();

    $('#form').submit(function() {
        if (state.participating) {
            participation.rename();
        } else {
            participation.join();
        }
        return false;
    });
    $('#disconnect').attr('disabled', 'disabled');
    setStatus('Controls disabled');


    //ws.onopen = function() {
    //    $('#name').change();
    //};
});



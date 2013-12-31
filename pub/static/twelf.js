CodeMirror.defineMode("twelf", function() {
  return {
    startState: function() {return {newDef: true};},
    token: function(stream, state) {
      if (stream.peek() == '%') {
        stream.next();
        if (stream.peek() == ' ') {
          stream.skipToEnd();
          return "comment";
        } else {
          stream.skipTo(' ') || stream.skipToEnd();
          state.newDef = false;
          return "keyword";
        }
      } else if (state.newDef) {
        if (stream.skipTo(":")) {
          state.newDef = false;
        } else {
          stream.skipTo('%') || stream.skipToEnd();
        }
        return "string";
      } else {
        if (stream.skipTo(".")) {
          stream.next();
          state.newDef = true;
        } else {
          stream.skipTo('%') || stream.skipToEnd();
        }
        return null;
      }
    }
  };
});

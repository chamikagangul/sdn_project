function deleteNote(noteId) {
  fetch("/delete-note", {
    method: "POST",
    body: JSON.stringify({ noteId: noteId }),
  }).then((_res) => {
    window.location.href = "/";
  });
}

function blockHost(ip) {
  fetch("/blacklist/block", {
    method: "POST",
    body: JSON.stringify({ ip: ip }),
  }).then((_res) => {
    // alert("Host " + ip + " blocked");
    location.reload();
  });
}

function unblockHost(ip) {
  fetch("/blacklist/unblock", {
    method: "POST",
    body: JSON.stringify({ ip: ip }),
  }).then((_res) => {
    // alert("Host " + ip + " unblocked");
    location.reload();
  });
}

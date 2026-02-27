function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function toggleLike(postId) {
    fetch(`/posts/${postId}/like`, {
        method: "PUT",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
    })
    .then(response => response.json())
    .then(data => {
        const btn = document.querySelector(`#like-btn-${postId}`);
        if (data.liked) {
            btn.classList.add("liked");
        } else {
            btn.classList.remove("liked");
        }
        btn.innerHTML = `<span class="heart">&#9829;</span> <span id="like-count-${postId}">${data.likes}</span>`;
    });
}

function deletePost(postId) {
    if (!confirm("Delete this post? This cannot be undone.")) return;

    fetch(`/posts/${postId}/delete`, {
        method: "DELETE",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            const card = document.querySelector(`#post-${postId}`);
            if (card) {
                card.style.transition = "opacity 0.25s";
                card.style.opacity = "0";
                setTimeout(() => card.remove(), 250);
            }
        }
    });
}

function editPost(postId) {
    const contentEl = document.querySelector(`#content-${postId}`);
    const editBtn = document.querySelector(`#edit-btn-${postId}`);
    if (!contentEl || !editBtn) return;

    const originalContent = contentEl.textContent.trim();
    editBtn.style.display = "none";

    const textarea = document.createElement("textarea");
    textarea.className = "edit-textarea";
    textarea.value = originalContent;
    textarea.rows = 3;
    contentEl.replaceWith(textarea);
    textarea.focus();

    const saveBtn = document.createElement("button");
    saveBtn.className = "btn-save";
    saveBtn.textContent = "Save";
    textarea.insertAdjacentElement("afterend", saveBtn);

    saveBtn.onclick = function () {
        const newContent = textarea.value.trim();
        if (!newContent) return;

        fetch(`/posts/${postId}/edit`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify({ content: newContent }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.content) {
                const newP = document.createElement("p");
                newP.className = "post-content";
                newP.id = `content-${postId}`;
                newP.textContent = data.content;
                textarea.replaceWith(newP);
                saveBtn.remove();
                editBtn.style.display = "";
            }
        });
    };
}

const text = "Welcome to the Typing Animation Example!";
const typingText = document.getElementById("typing-text");
const cursor = document.getElementById("cursor");

let index = 0;

function typeText() {
    if (index < text.length) {
        typingText.innerHTML += text.charAt(index);
        index++;
        setTimeout(typeText, 100);
    }
}

typeText();
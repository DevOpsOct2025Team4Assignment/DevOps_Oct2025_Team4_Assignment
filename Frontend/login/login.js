async function validateForm() {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!username || !password) {
        alert("Please fill in all fields.");
        return false;
    }

    try {
        const response = await fetch("http://localhost:5000/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "include", // important if sessions
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            alert("Invalid username or password");
            return false;
        }

        if (data.is_admin === 1) {
            window.location.href = "../Admin/AdminDashboard.html";
        } else {
            window.location.href = "../User/UserDashboard.html";
        }

    } catch (err) {
        alert("Server error. Please try again later.");
        console.error(err);
    }

    return false;
}

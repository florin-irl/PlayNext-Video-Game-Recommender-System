const API_BASE_URL = "http://127.0.0.1:8000";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form");
  if (form) {
    form.addEventListener("submit", handleFormSubmit);
  }
});

async function handleFormSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const formData = new FormData(form);

  // Differentiate between login and register forms
  if (form.id === "login-form") {
    const loginData = new URLSearchParams();
    loginData.append("username", formData.get("email"));
    loginData.append("password", formData.get("password"));

    try {
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: "POST",
        body: loginData,
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Login failed");
      }

      const data = await response.json();

      // Store token and user info securely
      localStorage.setItem("accessToken", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));

      // CRITICAL: Check if the user is initialized
      if (data.user.is_initialized) {
        window.location.href = "home.html"; // Redirect to main dashboard
      } else {
        window.location.href = "onboarding.html"; // Redirect to game selection
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  } else if (form.id === "register-form") {
    const password = formData.get("password");
    const confirmPassword = formData.get("confirm-password");

    if (password !== confirmPassword) {
      alert("Passwords do not match!");
      return;
    }

    const registerData = {
      email: formData.get("email"),
      username: formData.get("username"),
      password: password,
    };

    try {
      const response = await fetch(`${API_BASE_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(registerData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Registration failed");
      }

      alert("Registration successful! Please log in.");
      window.location.href = "login.html"; // Redirect to login page
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  }
}

const API_BASE = "/api/v1";

function showMessage(message) {
  document.getElementById("messageBox").textContent =
    typeof message === "string" ? message : JSON.stringify(message, null, 2);
}

async function registerUser() {
  const username = document.getElementById("registerUsername").value.trim();
  const password = document.getElementById("registerPassword").value.trim();

  if (!username || !password) {
    showMessage("Preencha usuário e senha para cadastro.");
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ username, password })
    });

    const data = await response.json();

    if (!response.ok) {
      showMessage(data.detail || "Erro ao cadastrar usuário.");
      return;
    }

    showMessage(data);
  } catch (error) {
    showMessage(`Erro de conexão no cadastro: ${error.message}`);
  }
}

async function loginUser() {
  const username = document.getElementById("loginUsername").value.trim();
  const password = document.getElementById("loginPassword").value.trim();

  if (!username || !password) {
    showMessage("Preencha usuário e senha para login.");
    return;
  }

  try {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    const response = await fetch(`${API_BASE}/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: formData
    });

    const data = await response.json();

    if (!response.ok) {
      showMessage(data.detail || "Erro no login.");
      return;
    }

    localStorage.setItem("access_token", data.access_token);
    showMessage("Login realizado com sucesso. Token armazenado.");
  } catch (error) {
    showMessage(`Erro de conexão no login: ${error.message}`);
  }
}

async function callPredict() {
  const token = localStorage.getItem("access_token");

  if (!token) {
    showMessage("Você precisa fazer login antes de chamar o predict.");
    return;
  }

  const modelVersion = document.getElementById("modelVersion").value;

  const payload = {
    MedInc: parseFloat(document.getElementById("MedInc").value),
    HouseAge: parseFloat(document.getElementById("HouseAge").value),
    AveRooms: parseFloat(document.getElementById("AveRooms").value),
    AveBedrms: parseFloat(document.getElementById("AveBedrms").value),
    Population: parseFloat(document.getElementById("Population").value),
    AveOccup: parseFloat(document.getElementById("AveOccup").value),
    Latitude: parseFloat(document.getElementById("Latitude").value),
    Longitude: parseFloat(document.getElementById("Longitude").value)
  };

  const hasInvalidField = Object.values(payload).some(value => Number.isNaN(value));

  if (hasInvalidField) {
    showMessage("Preencha todos os campos numéricos da previsão.");
    return;
  }

  try {
    const response = await fetch(`/api/${modelVersion}/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (!response.ok) {
      showMessage(data.detail || "Erro ao chamar predict.");
      return;
    }

    showMessage({
      mensagem: "Predição realizada com sucesso",
      versao: data.versao,
      usuario: data.usuario,
      prediction_model: data.prediction_model,
      prediction_dollars: data.prediction_dollars
    });
  } catch (error) {
    showMessage(`Erro de conexão no predict: ${error.message}`);
  }
}

function fillExampleData() {
  document.getElementById("MedInc").value = 8.3252;
  document.getElementById("HouseAge").value = 41.0;
  document.getElementById("AveRooms").value = 6.984127;
  document.getElementById("AveBedrms").value = 1.02381;
  document.getElementById("Population").value = 322.0;
  document.getElementById("AveOccup").value = 2.555556;
  document.getElementById("Latitude").value = 37.88;
  document.getElementById("Longitude").value = -122.23;

  showMessage("Campos preenchidos com exemplo do dataset.");
}

function logoutUser() {
  localStorage.removeItem("access_token");
  showMessage("Logout realizado. Token removido.");
}

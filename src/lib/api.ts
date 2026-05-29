const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

class ApiError extends Error {
  public status: number;
  public data: any;
  
  constructor(status: number, data: any) {
    super(data.message || data.detail || "An unexpected error occurred");
    this.status = status;
    this.data = data;
    this.name = "ApiError";
  }
}

async function handleResponse(response: Response) {
  let data;
  try {
    data = await response.json();
  } catch (e) {
    data = null;
  }

  if (!response.ok) {
    throw new ApiError(response.status, data || { message: response.statusText });
  }

  return data;
}

function getHeaders(isFormData = false): HeadersInit {
  const headers: Record<string, string> = {};
  
  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }

  // Token is stored in localStorage by the AuthProvider
  const token = localStorage.getItem("ampaware.auth.token");
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  return headers;
}

export const api = {
  get: async (endpoint: string) => {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: "GET",
      headers: getHeaders(),
    });
    return handleResponse(response);
  },

  post: async (endpoint: string, body: any, isFormData = false) => {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: "POST",
      headers: getHeaders(isFormData),
      body: isFormData ? body : JSON.stringify(body),
    });
    return handleResponse(response);
  },

  put: async (endpoint: string, body: any) => {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: "PUT",
      headers: getHeaders(),
      body: JSON.stringify(body),
    });
    return handleResponse(response);
  },

  delete: async (endpoint: string) => {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: "DELETE",
      headers: getHeaders(),
    });
    return handleResponse(response);
  },
};

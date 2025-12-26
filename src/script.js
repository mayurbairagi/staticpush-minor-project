async function deploySite() {
  const fileInput = document.getElementById("zipFile");
  const status = document.getElementById("status");
  const result = document.getElementById("result");

  if (!fileInput.files.length) {
    status.textContent = "❌ Please select a ZIP file.";
    return;
  }

  const file = fileInput.files[0];

  status.textContent = "⏳ Deploying your site...";
  result.textContent = "";

  try {
    // 1️⃣ Convert ZIP to Base64
    const base64Data = await fileToBase64(file);




    // 2️⃣ Call API
const API_ENDPOINT = "YOUR_API_GATEWAY_URL_HERE";

const response = await fetch(API_ENDPOINT, {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    zip: base64Data
  })
});


    // 3️⃣ Parse response
    const data = await response.json();

    // 4️⃣ Handle backend error
    if (!response.ok) {
      throw new Error(data.error || "Deployment failed");
    }

    // 5️⃣ Extract URL safely (PERMANENT FIX)
    const siteUrl =
      data.url ||
      data.website_url ||
      (data.body && data.body.url);

    if (!siteUrl) {
      throw new Error("Deployment succeeded but URL was not returned");
    }

    // 6️⃣ Update UI
    status.textContent = "✅ Deployment successful!";
    result.innerHTML = `
      🌐 Live URL:
      <a href="${siteUrl}" target="_blank">${siteUrl}</a>
    `;

  } catch (err) {
    status.textContent = "❌ Error occurred";
    result.textContent = err.message;
  }
}

// Helper function (DO NOT TOUCH)
function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      resolve(reader.result.split(",")[1]);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

import dicomParser from 'dicom-parser';
import cornerstone from 'cornerstone-core';
import cornerstoneWADOImageLoader from 'cornerstone-wado-image-loader';

// Initialize cornerstone loader
cornerstoneWADOImageLoader.external.cornerstone = cornerstone;

async function loadDicomImage(dicomPath) {
    return new Promise((resolve, reject) => {
        fetch(dicomPath)
            .then(response => response.arrayBuffer())
            .then(buffer => {
                const dataset = dicomParser.parseDicom(new Uint8Array(buffer));
                resolve(dataset);
            })
            .catch(reject);
    });
}

function selectBestFrames(frames) {
    const numFrames = frames.length;

    // Middle frame
    const middleFrame = frames[Math.floor(numFrames / 2)];

    // Frame with max intensity
    const maxIntensityFrame = frames.reduce((best, frame) => {
        const sum = frame.reduce((acc, pixel) => acc + pixel, 0);
        return sum > best.sum ? { sum, frame } : best;
    }, { sum: 0, frame: null }).frame;

    // Frame with largest ROI (non-zero pixels)
    const largestRoiFrame = frames.reduce((best, frame) => {
        const count = frame.filter(pixel => pixel > 0).length;
        return count > best.count ? { count, frame } : best;
    }, { count: 0, frame: null }).frame;

    // Frame with most edges (simple Sobel filter logic)
    const edgeDetection = frame => {
        // Simplified edge detection logic (mock implementation)
        return frame.filter(pixel => pixel > 128).length;
    };
    const edgesFrame = frames.reduce((best, frame) => {
        const edgeCount = edgeDetection(frame);
        return edgeCount > best.edgeCount ? { edgeCount, frame } : best;
    }, { edgeCount: 0, frame: null }).frame;

    return {
        middle: middleFrame,
        maxIntensity: maxIntensityFrame,
        largestRoi: largestRoiFrame,
        edges: edgesFrame,
    };
}

function normalizeAndSave(frame, filename) {
    // Normalize pixel values and display on canvas or save
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = frame.width;
    canvas.height = frame.height;

    const imageData = ctx.createImageData(canvas.width, canvas.height);
    for (let i = 0; i < frame.length; i++) {
        const pixelValue = Math.min(255, Math.max(0, frame[i])); // Normalize
        imageData.data[i * 4] = pixelValue;    // R
        imageData.data[i * 4 + 1] = pixelValue; // G
        imageData.data[i * 4 + 2] = pixelValue; // B
        imageData.data[i * 4 + 3] = 255;       // Alpha
    }
    ctx.putImageData(imageData, 0, 0);

    canvas.toDataURL('image/jpeg');
}

async function processDicom(dicomPath, outputFolder) {
    const dataset = await loadDicomImage(dicomPath);
    const frames = extractFramesFromDataset(dataset);

    const selectedFrames = selectBestFrames(frames);
    for (const [method, frame] of Object.entries(selectedFrames)) {
        normalizeAndSave(frame, `${outputFolder}/${method}.jpg`);
    }
}

// Usage example
const dicomPath = '"C:\\Users\\Rahul\\Downloads\\image.dcm"';
const outputFolder = 'output_images';
processDicom(dicomPath, outputFolder);

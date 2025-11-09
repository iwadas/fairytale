const getSrc = (src) => {
    if (src.startsWith("blob:")) {
        return src;
    } else {
        return `http://localhost:8000/${src}`;
    }
};

export default getSrc;
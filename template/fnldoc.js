/**
 * @param name {string}
 * @param htmlContent {string}
 * @param contentSetter {string => void}
 */
const createTocLeaf = (name, htmlContent, contentSetter) => {
    const li = document.createElement("li");
    li.setAttribute("class", "fnldoc--toc--point fnldoc--toc--leaf");

    const link = document.createElement("a");
    link.href = "#";
    link.innerText = name
    link.addEventListener("click", () => {
        contentSetter(htmlContent);
    });
    li.appendChild(link);
    return li;
}

/**
 * @param name {string}
 * @param content {Record<string, any>}
 * @param contentSetter {string => void}
 */
const createTocBranch = (name, content, contentSetter) => {
    const li = document.createElement("li");
    li.innerText = name + " ";
    li.setAttribute("class", "fnldoc--toc--point fnldoc--toc--node");

    const buttonSpan = document.createElement("button");
    buttonSpan.innerText = "+";
    buttonSpan.setAttribute("class", "fnldoc--toc--toggle")
    buttonSpan.addEventListener("click", () => {
        if (buttonSpan.innerText === "-") {
            buttonSpan.innerText = "+";
            nav.style.visibility = "hidden";
        } else {
            buttonSpan.innerText = "-";
            nav.style.visibility = "visible";
        }
    });
    li.appendChild(buttonSpan);

    const nav = document.createElement("nav");
    nav.appendChild(tocToBulletList(content, contentSetter));
    nav.style.visibility = "hidden";

    li.appendChild(nav);
    return li;
}

/**
 * @param toc {Record<string, any>}
 * @param contentSetter {string => void}
 */
const tocToBulletList = (toc, contentSetter) => {
    const list = document.createElement("ul");
    for (const [name, content] of Object.entries(toc))
        if (typeof content === "string")
            list.appendChild(createTocLeaf(name, content, contentSetter));
        else
            list.appendChild(createTocBranch(name, content, contentSetter));
    return list;
};

/**
 * @param conditionFn { () => boolean }
 * @param stepMs { number= }
 */
const waitForCondition = (conditionFn, stepMs=100) =>
    new Promise((resolve, reject) => {
        const intervalId = setInterval(
            () => {
                if (conditionFn()){
                    clearInterval(intervalId);
                    resolve();
                }
            },
            stepMs
        );
    });


/**
 * @param {{tocDiv: HTMLDivElement}}
 */
window.fnlDoc = async ({tocDiv}) => {
    await waitForCondition(() => window.fnlDocData !== undefined);


    const contentSetter = html => {
        console.log({html});
    };

    const data = window.fnlDocData;
    const element = tocToBulletList(data, contentSetter);
    tocDiv.appendChild(element);
};

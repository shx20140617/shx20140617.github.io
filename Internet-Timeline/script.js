document.addEventListener('DOMContentLoaded', function() {
    const timelineData = [
                             {
                                 "year": 1969,
                                 "title": 'ARPANET 诞生',
                                 "description": 'ARPANET 是现代互联网的前身，它首次向大家展示了计算机网络的潜力。',
                                 "image": 'assets/ARPANET.png',
                                 "moreInfo": 'ARPANET，于1969年由美国高级研究计划局创建，是互联网的前身。它采用分组交换技术连接多个科研机构和大学，成功实现了计算机之间的远程通信，为现代网络技术奠定了坚实的基础。',
                                  "link": 'https://hr.edu.cn/xueshu/202208/t20220809_2241033.shtml'
                             },
                             {
                                 "year": 1983,
                                 "title": "TCP/IP 协议成为标准",
                                 "description": "TCP/IP 协议的采用标志着互联网通信标准的确立，为全球网络互联奠定了基础。",
                                 "image": "assets/TCP_IP.png",
                                 "moreInfo": "TCP/IP协议使不同网络能够互联，推动了互联网的全球化发展，为全球互联提供了基础。它通过标准化的通信规则，让不同厂商的设备能够无缝连接。TCP/IP协议采用分层架构，包括应用层、传输层、网络层和链路层，每一层负责特定功能。其中，IP协议负责数据包的路由和转发，而TCP协议则确保数据传输的可靠性。这种设计不仅支持多种网络类型，还适应了不断增长的网络需求。",
                                 "link": "https://baike.baidu.com/item/TCP%2FIP%E5%8D%8F%E8%AE%AE/212915"
                             },
                             {
                                 "year": 1990,
                                 "title": "万维网（WWW）诞生",
                                 "description": "蒂姆·伯纳斯-李发明了万维网，使互联网信息共享变得更加便捷。",
                                 "image": "assets/WWW.png",
                                 "moreInfo": "万维网的出现彻底改变了人们获取信息的方式，极大地推动了知识的传播和全球化的进程。它通过网页和超链接的形式，将全球范围内的信息资源整合在一起，让人们能够快速、便捷地访问和分享各种知识，无论身处何地，都能轻松获取海量信息，促进了文化的交流与融合。",
                                 "link": "https://baike.baidu.com/item/WWW/109924"
                             },
                             {
                                 "year": 1994,
                                 "title": "亚马逊成立",
                                 "description": "亚马逊的成立标志着电子商务的兴起，改变了人们的购物方式。",
                                 "image": "assets/Amazon.png",
                                 "moreInfo": "亚马逊作为电子商务领域的先锋，引领了全球电子商务革命，极大地推动了在线零售的快速发展。它凭借强大的物流体系、丰富的产品种类和便捷的购物体验，改变了人们的购物习惯，将传统的线下购物模式逐步转移到线上，为全球消费者提供了前所未有的便利和选择。",
                                 "link": "https://baike.baidu.com/item/%e4%ba%9a%e9%a9%ac%e9%80%8a/21766"
                             },
                             {
                                 "year": 1998,
                                 "title": "谷歌成立",
                                 "description": "谷歌的成立彻底改变了人们搜索和获取信息的方式。",
                                 "image": "assets/Google.png",
                                 "moreInfo": "谷歌的成立彻底改变了人们搜索和获取信息的方式。通过不断优化的搜索算法，谷歌能够快速准确地提供相关结果，极大地提升了信息检索的效率。如今，谷歌的AI技术进一步革新了搜索体验，不仅能理解复杂的自然语言，还能根据用户的搜索历史和偏好提供个性化结果。这种智能化的搜索方式不仅节省了用户的时间，还让信息获取变得更加便捷和高效。",
                                 "link": "https://baike.baidu.com/item/google/86964"
                             },
                             {
                                 "year": 2004,
                                 "title": "Facebook 上线",
                                 "description": "Facebook 的推出开启了社交网络的新时代，改变了人们的社交方式。",
                                 "image": "assets/Facebook.png",
                                 "moreInfo": "Facebook的推出开启了社交网络的新时代，连接了全球数十亿用户，重塑了社交互动和信息传播的方式。通过强大的社交功能，Facebook打破了地理限制，让人们能够随时随地与朋友、家人保持联系，分享生活点滴。这种便捷性不仅促进了全球范围内的信息快速传播，还推动了文化交流和理解。",
                                 "link": "https://baike.baidu.com/item/Facebook/62103271"
                             },
                             {
                                 "year": 2009,
                                 "title": "比特币诞生",
                                 "description": "比特币的诞生标志着区块链技术的应用，开启了加密货币时代。",
                                 "image": "assets/bitcoin.png",
                                 "moreInfo": "比特币推动了去中心化金融的发展，改变了传统金融体系。它通过区块链技术实现了点对点的交易，无需依赖传统银行等中介机构，极大地降低了跨境交易成本并提高了交易速度。比特币的去中心化特性赋予用户更大的财务自主权，使他们能够直接管理自己的资产，而不必受制于传统金融机构。",
                                 "link": "https://baike.baidu.com/item/%E6%AF%94%E7%89%B9%E5%B8%81/4143690"
                             },
                             {
                                 "year": 2010,
                                 "title": "Instagram 上线",
                                 "description": "Instagram 的推出改变了图片分享和社交媒体的格局。",
                                 "image": "assets/Instagram.png",
                                 "moreInfo": "Instagram凭借其强大的图片和视频分享功能，推动了视觉内容创作的兴起，极大地影响了社交媒体文化。它让用户能够轻松创作并分享高质量的视觉作品，激发了创意表达，改变了人们记录生活和社交互动的方式。",
                                 "link": "https://baike.baidu.com/item/Instagram/8550544"
                             },
                             {
                                 "year": 2014,
                                 "title": "HTTP/2 发布",
                                 "description": "HTTP/2 的发布显著提升了互联网传输效率，优化了网页加载速度。",
                                 "image": "assets/http2.png",
                                 "moreInfo": "HTTP/2的发布显著提升了互联网传输效率，优化了网页加载速度。它通过多路复用、头部压缩和服务器推送等技术，减少了网络延迟，使网页内容能够更快地呈现给用户，大大改善了浏览体验。",
                                 "link": "https://info.support.huawei.com/info-finder/encyclopedia/zh/HTTP--2.html"
                             },
                             {
                                 "year": 2016,
                                 "title": "Let's Encrypt 普及 HTTPS",
                                 "description": "Let's Encrypt 提供免费 SSL 证书，推动了 HTTPS 的广泛采用。",
                                 "image": "assets/lets_encrypt.png",
                                 "moreInfo": "Let's Encrypt 提供免费 SSL 证书，推动了 HTTPS 的广泛采用。它通过自动化工具如 Certbot，简化了证书申请和续期流程，降低了 HTTPS 部署门槛。这使得更多网站能够轻松实现数据加密，提升用户数据安全性和网站可信度。",
                                 "link": "https://baike.baidu.com/item/Let%27s/7539260"
                             },
                             {
                                 "year": 2020,
                                 "title": "5G 商用启动",
                                 "description": "5G 技术的商用开启了高速、低延迟通信的新时代。",
                                 "image": "assets/5g.png",
                                 "moreInfo": "5G技术的商用开启了高速、低延迟通信的新时代，其超高速率、低延迟和大连接能力为社会带来深远影响。5G不仅提升了用户体验，还推动了自动驾驶、远程医疗、智能工厂等领域的创新应用，加速了各行业的数字化转型。",
                                 "link": "https://baike.baidu.com/item/5g/29780"
                             },
                             {
                                 "year": 2021,
                                 "title": "元宇宙概念爆发",
                                 "description": "元宇宙概念的兴起标志着虚拟与现实融合的新趋势。",
                                 "image": "assets/metaverse.png",
                                 "moreInfo": "元宇宙推动了虚拟现实和数字经济的发展，重塑了未来生活方式。它通过虚拟现实、增强现实等技术，让用户在沉浸式环境中社交、娱乐和办公。同时，元宇宙为数字经济开辟了新空间，用户可以创建和交易数字资产，催生新的商业模式。这种融合现实与虚拟的方式，将深刻改变人类的生产、消费和精神生活。",
                                 "link": "https://baike.baidu.com/item/%E5%85%83%E5%AE%87%E5%AE%99/58292530"
                             },
                             {
                                 "year": 2022,
                                 "title": "Web3 兴起",
                                 "description": "Web3 的兴起标志着去中心化互联网的新时代。",
                                 "image": "assets/Web3.png",
                                 "moreInfo": "Web3强调用户数据主权，推动了去中心化应用的发展。它通过区块链技术，让用户掌控自己的数据，确保隐私安全。在Web3中，数据存储于分布式网络，用户可自主决定数据的使用和分享。这种去中心化的架构不仅提升了数据安全性，还为创作者和用户提供了更公平的经济模式。",
                                 "link": "https://baike.baidu.com/item/web3.0/4873257"
                             },
                             {
                                 "year": 2023,
                                 "title": "AI 技术快速发展",
                                 "description": "AI 技术快速发展，推动各行各业智能化升级。",
                                 "image": "assets/AI-Tools.png",
                                 "moreInfo": "互联网的发达使得 AI 技术的数据稀缺问题得到解决，于是互联网催生出了大语言模型。AI 技术快速发展，推动各行各业智能化升级。通过深度学习、自然语言处理等先进算法，AI 能够模拟人类智能进行复杂任务，如图像识别、语音交互和预测分析。这不仅提高了生产效率，还为个性化服务和创新解决方案提供了可能，极大地改善了人们的日常生活、工作和学习效率。",
                                 "link": "https://baike.baidu.com/item/%E5%A4%A7%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B/62884793"
                             }
                         ];

            const timelineContainer = document.querySelector('.timeline');

            timelineData.forEach((item, index) => {
                const timelineItem = document.createElement('div');
                timelineItem.classList.add('timeline-container');
                timelineItem.classList.add(index % 2 === 0 ? 'left' : 'right');

                timelineItem.innerHTML = `
                    <div class="timeline-content">
                        <h3>${item.year}</h3>
                        <h4>${item.title}</h4>
                        <p>${item.description}</p>
                    </div>
                    <div class="timeline-popup">
                        <img src="${item.image}" alt="${item.title}">
                        <h4>${item.title}</h4>
                        <p>${item.moreInfo}</p>
                        <a href="${item.link}" target="_blank">了解更多</a>
                    </div>
                `;

                timelineContainer.appendChild(timelineItem);

                // 添加鼠标悬停事件
                const content = timelineItem.querySelector('.timeline-content');
                const popup = timelineItem.querySelector('.timeline-popup');

                // 创建一个标志变量，用于判断是否在悬浮窗口或栏目内
                let isHovering = false;

                // 鼠标进入时间线栏目或悬浮窗口时显示悬浮窗口
                content.addEventListener('mouseenter', () => {
                    isHovering = true;
                    popup.style.display = 'block';
                });

                popup.addEventListener('mouseenter', () => {
                    isHovering = true;
                });

                // 鼠标离开时间线栏目或悬浮窗口时隐藏悬浮窗口
                content.addEventListener('mouseleave', () => {
                    setTimeout(() => {
                        if (!isHovering) {
                            popup.style.display = 'none';
                        }
                    }, 100); // 延迟隐藏，避免快速移动时闪烁
                });

                popup.addEventListener('mouseleave', () => {
                    isHovering = false;
                    popup.style.display = 'none';
                });
            });



    // 知识问答数据
    const quizData = [
                     {
                     question: '互联网的雏形是什么？',
                     options: ['ARPANET', 'WWW', 'TCP/IP', 'HTTP'],
                     answer: 'ARPANET'
                     },
                     {
                     question: '谁提出了万维网的概念？',
                     options: ['比尔·盖茨', '史蒂夫·乔布斯', '蒂姆·伯纳斯-李', '林纳斯·托瓦兹'],
                     answer: '蒂姆·伯纳斯-李'
                     },
                     {
                     question: '以下哪个是电子商务的代表？',
                     options: ['Google', 'Facebook', 'Amazon', 'YouTube'],
                     answer: 'Amazon'
                     },
                     {
                     question: '以下哪个协议用于在互联网上传输网页？',
                     options: ['FTP', 'SMTP', 'HTTP', 'DNS'],
                     answer: 'HTTP'
                     },
                     {
                     question: '哪个公司开发了第一个广泛使用的网络浏览器？',
                     options: ['Microsoft', 'Netscape', 'Google', 'Apple'],
                     answer: 'Netscape'
                     },
                     {
                     question: 'IPv4地址由多少位组成？',
                     options: ['32', '64', '128', '256'],
                     answer: '32'
                     },
                     {
                     question: '以下哪个是用于加密网络通信的协议？',
                     options: ['HTTP', 'FTP', 'SSL/TLS', 'SMTP'],
                     answer: 'SSL/TLS'
                     },
                     {
                     question: '哪个搜索引擎在1998年由拉里·佩奇和谢尔盖·布林创建？',
                     options: ['Bing', 'Yahoo', 'Google', 'DuckDuckGo'],
                     answer: 'Google'
                     },
                     {
                     question: '以下哪个是社交媒体平台？',
                     options: ['LinkedIn', 'Dropbox', 'Slack', 'Trello'],
                     answer: 'LinkedIn'
                     },
                     {
                     question: '哪个术语用于描述互联网上的恶意软件？',
                     options: ['Firewall', 'Malware', 'Phishing', 'Spyware'],
                     answer: 'Malware'
                     },
                     {
                     question: '哪个技术允许在互联网上进行语音和视频通话？',
                     options: ['VoIP', 'VPN', 'DNS', 'ISP'],
                     answer: 'VoIP'
                     },
                     {
                     question: 'HTTP/2 是在什么时候发布的？',
                     options: ['2011年', '2014年', '2013年', '2015年'],
                     answer: '2014年'
                     }
                     ];

    const questionEl = document.getElementById('question');
    const optionsEl = document.getElementById('options');
    const submitBtn = document.getElementById('submit-btn');
    const resultEl = document.getElementById('result');

    function getRandomQuestions(data, count) {
        const shuffled = [...data].sort(() => 0.5 - Math.random());
        return shuffled.slice(0, count);
    }


    const randomQuestions = getRandomQuestions(quizData, 3);

    let currentQuestionIndex = 0;
    let score = 0;

    function loadQuestion() {
        const currentQuestion = randomQuestions[currentQuestionIndex];
        questionEl.textContent = currentQuestion.question;
        optionsEl.innerHTML = '';

        currentQuestion.options.forEach(option => {
            const button = document.createElement('button');
            button.textContent = option;
            button.addEventListener('click', () => selectAnswer(option));
            optionsEl.appendChild(button);
        });
    }

    function selectAnswer(answer) {
        if (answer === randomQuestions[currentQuestionIndex].answer) {
            score++;
        }
    }

    submitBtn.addEventListener('click', () => {
        currentQuestionIndex++;
        if (currentQuestionIndex < randomQuestions.length) {
            loadQuestion();
        } else {
            resultEl.textContent = `你的得分：${score} / ${randomQuestions.length}`;
            questionEl.textContent = '';
            optionsEl.innerHTML = '';
            submitBtn.style.display = 'none';
        }
    });

    loadQuestion();
});

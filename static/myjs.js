// like update function client
function toggle_like(post_id, type) {
    console.log(post_id, type);
    let $a_like = $(`#${post_id} a[aria-label='${type}']`);
    let $i_like = $a_like.find("i");

    let full_icons = {"heart" : "fa-heart", "like" : "fa-thumbs-up", "star" : "fa-star"};

    let empty_icons = {"heart" : "fa-heart-o", "like" : "fa-thumbs-o-up", "star" : "fa-star-o"};

    if ($i_like.hasClass(full_icons[type])) {
        $.ajax({
            type: "POST",
            url: "/update_like",
            data: {
                post_id_give: post_id,
                type_give: type,
                action_give: "unlike"
            },
            success: function (response) {
                console.log("unlike")
                $i_like.addClass(empty_icons[type]).removeClass(full_icons[type]);
                $a_like.find("span.like-num").text(num2str(response["count"]));
            }
        })
    } else {
        $.ajax({
            type: "POST",
            url: "/update_like",
            data: {
                post_id_give: post_id,
                type_give: type,
                action_give: "like"
            },
            success: function (response) {
                console.log("like");
                $i_like.addClass(full_icons[type]).removeClass(empty_icons[type]);
                $a_like.find("span.like-num").text(num2str(response["count"]));
            }
        })

    }
};

// posting function
function post() {
    let comment = $("#textarea-post").val();
    let today = new Date().toISOString();
    $.ajax({
        type: "POST",
        url: "/posting",
        data: {
            comment_give: comment,
            date_give: today
        },
        success: function (response) {
            $("#modal-post").removeClass("is-active");
            window.location.reload();
        }
    })
}

// posting time 나타내기
function time2str(date) {
    let today = new Date();
    let time = (today - date) / 1000 / 60;  // 분

    if (time < 60) {
        return parseInt(time) + "분 전";
    }
    time = time / 60  // 시간
    if (time < 24) {
        return parseInt(time) + "시간 전";
    }
    time = time / 24;
    if (time < 7) {
        return parseInt(time) + "일 전";
    }
    return `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일`;
};

// like number 형식
function num2str(count) {
    if (count > 10000) {
        return parseInt(count / 1000) + "k";
    }
    if (count > 500) {
        return parseInt(count / 100) / 10 + "k";
    }
    if (count == 0) {
        return "";
    }
    return count;
};

// posting card 만들기
function get_posts(username) {

    // if문 [만약 username이 아니라면?]
    if (username == undefined) {
        username = "";
    }

    $("#post-box").empty();
    $.ajax({
        type: "GET",
        url: `/get_posts?username_give=${username}`, // username의 코드를 받아오는 작업!
        data: {},
        success: function (response) {
            if (response["result"] == "success") {
                let posts = response["posts"];
                for (let i = 0; i < posts.length; i++) {
                    let post = posts[i];
                    let time_post = new Date(post["date"]);

                    // time_before로 원하는 data만 뽑아서 client에게 보여준다!
                    let time_before = time2str(time_post);

                    // heart 3항식
                    let class_heart = post['heart_by_me'] ? "fa-heart" : "fa-heart-o";

                    // count heart
                    let count_heart = post['count_heart'];

                    // like 3항식
                    let class_like = post['like_by_me'] ? "fa-thumbs-up" : "fa-thumbs-o-up";

                    // count like
                    let count_like = post['count_like'];

                    // star 3항식
                    let class_star = post['star_by_me'] ? "fa-star" : "fa-star-o";

                    // count star
                    let count_star = post['count_star'];

                    let html_temp = `<div class="box" id="${post["_id"]}">
                                        <article class="media">
                                            <div class="media-left">
                                                <a class="image is-64x64" href="/user/${post['username']}">
                                                    <img class="is-rounded" src="/static/${post['profile_pic_real']}"
                                                         alt="Image">
                                                </a>
                                            </div>
                                            <div class="media-content">
                                                <div class="content">
                                                    <p>
                                                        <strong>${post['profile_name']}</strong> <small>@${post['username']}</small> <small>${time_before}</small>
                                                        <br>
                                                        ${post['comment']}
                                                    </p>
                                                </div>
                                                <nav class="level is-mobile">
                                                    <div class="level-left">
                                                    
                                                        <!-- heart -->
                                                        <a class="level-item is-sparta" aria-label="heart" onclick="toggle_like('${post['_id']}', 'heart')">
                                                            <span class="icon is-small"><i class="fa ${class_heart}"
                                                                                           aria-hidden="true"></i></span>&nbsp;<span class="like-num">${num2str(count_heart)}</span>
                                                        </a>
                                                        
                                                        <!-- star -->
                                                        <a class="level-item is-sparta" aria-label="star" onclick="toggle_like('${post['_id']}', 'star')">
                                                            <span class="icon is-small"><i class="fa ${class_star}"
                                                                                           aria-hidden="true"></i></span>&nbsp;<span class="like-num">${num2str(count_star)}</span>
                                                        </a>
                                                        
                                                        <!-- like -->
                                                        <a class="level-item is-sparta" aria-label="like" onclick="toggle_like('${post['_id']}', 'like')">
                                                            <span class="icon is-small"><i class="fa ${class_like}"
                                                                                           aria-hidden="true"></i></span>&nbsp;<span class="like-num">${num2str(count_like)}</span>
                                                        </a>
                                                        
                                                    </div>

                                                </nav>
                                            </div>
                                        </article>
                                    </div>`;
                    $("#post-box").append(html_temp);
                }
            }
        }
    })
}

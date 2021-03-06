import torch as th


def trans_MNIST(pos: th.Tensor, a_t_next: th.Tensor, f: int, img_size: int) -> th.Tensor:
    """

    :param pos:
    :param a_t_next: Tensor of size = (2,)
    :param f:
    :param img_size:
    :return:
    """

    new_pos = pos.clone()

    idx = (new_pos[:, 0] + a_t_next[:, 0] >= 0) * \
          (new_pos[:, 0] + a_t_next[:, 0] + f < img_size) * \
          (new_pos[:, 1] + a_t_next[:, 1] >= 0) * \
          (new_pos[:, 1] + a_t_next[:, 1] + f < img_size)
    idx = idx.unsqueeze(1).to(th.float)

    return idx * (new_pos + a_t_next) + (1 - idx) * new_pos
